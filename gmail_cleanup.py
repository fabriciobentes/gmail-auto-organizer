import json
import os
import re
import sys
from typing import Dict, List

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CNPJ_PATTERN = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")

MONITORED_LABELS = [
    "99",
    "Amazon",
    "Âmbar",
    "Anhanguera",
    "Banco Brasil",
    "Banco Bradesco",
    "Banco PAN",
    "Cadê meu ônibus?",
    "Certificado Digital",
    "ChatGPT",
    "Claro",
    "Concursos e Vagas",
    "Cursos e Capacitação",
    "Docker",
    "GitHub",
    "Globo",
    "Google",
    "Gov",
    "IFAM",
    "Instagram",
    "iFood + 99Food",
    "Linkedin",
    "MEI",
    "Mercado Livre",
    "Mercado Pago",
    "Microsoft",
    "Motorola",
    "Netflix",
    "Notion",
    "Nubank",
    "Pinterest",
    "Samsung",
    "Santander",
    "Shopee",
    "Spotify",
    "Truedata",
    "Uber",
    "YouCine",
    "YouTube",
]

# Regras para aplicar automaticamente os marcadores.
# A busca nao fica limitada ao INBOX: assim, mensagens antigas ou ja arquivadas
# que ainda estejam sem o marcador tambem sao corrigidas.
BASE_AUTO_LABEL_RULES = {
    "99": "from:(99app.com)",
    "Amazon": "(from:(amazon.com) OR from:(amazon.com.br))",
    "Âmbar": "from:(ambarenergia-am.com.br)",
    "Anhanguera": (
        "(from:(anhanguera.com) OR "
        "from:(kroton.com.br) OR "
        "from:(cogna.com.br))"
    ),
    "Banco Brasil": (
        "(from:(bb.com.br) OR "
        "from:(bancodobrasil.com.br) OR "
        "from:(bancobrasil.com.br))"
    ),
    "Banco Bradesco": (
        "(from:(bradesco.com.br) OR "
        "from:(campanhasbradesco.com.br))"
    ),
    "Banco PAN": "(from:(pan.com.vc) OR from:(pancartoes.com.br))",
    "Cadê meu ônibus?": (
        "(from:(sinetram.com.br) OR "
        "from:(prodatamobility.com.br))"
    ),
    "Certificado Digital": (
        "(from:(soluti.com.br) OR "
        "from:(gfsis.com.br) OR "
        "subject:(\"Certificado Digital\"))"
    ),
    "ChatGPT": (
        "((from:(openai.com) OR "
        "from:(mail.openai.com) OR "
        "from:(tm.openai.com)) OR "
        "(from:(ebanx.com) subject:(OpenAI)))"
    ),
    "Claro": "(from:(claro.com.br) OR from:(minhaclaro.com.br))",
    "Concursos e Vagas": (
        "(from:(fgv.br) OR "
        "from:(ibfc.com.br) OR "
        "from:(institutoconsulplan.org.br) OR "
        "from:(indeed.com) OR "
        "from:(recrutei-mail.com.br))"
    ),
    "Cursos e Capacitação": (
        "(from:(netacad.com) OR "
        "from:(devtitans@icomp.ufam.edu.br) OR "
        "from:(intelbras-info.com) OR "
        "from:(passeidireto.com) OR "
        "from:(descomplica.com.br))"
    ),
    "Docker": "from:(docker.com)",
    "GitHub": "from:(github.com)",
    "Globo": (
        "(from:(cadastro@globo.com) OR "
        "from:(mkt.cartolafc.globo.com))"
    ),
    "Google": "from:(google.com)",
    "Gov": "from:(gov.br)",
    "IFAM": (
        "(from:(ifam.edu.br) OR to:(ifam.edu.br) OR "
        "subject:(PCCT) OR subject:(PPCT))"
    ),
    "Instagram": "from:(instagram.com)",
    "iFood + 99Food": (
        "(from:(ifood.com.br) OR "
        "from:(ifood-no-reply.com) OR "
        "from:(99food@br.didiglobal.com) OR "
        "from:(99food@mkt-br.didiglobal.com))"
    ),
    "Linkedin": "from:(linkedin.com)",
    "MEI": (
        "(from:(meumeiassessoria.com.br) OR "
        "from:(meumeidigital.com.br) OR "
        "from:(meiportalmicroempreendedor.com.br) OR "
        "from:(maismei.com.br) OR "
        "from:(regularizacaomei.com.br) OR "
        "subject:(MEI) OR "
        "subject:(DAS-SIMEI))"
    ),
    "Mercado Livre": "(from:(mercadolivre.com.br) OR from:(mercadolivre.com))",
    "Mercado Pago": "(from:(mercadopago.com.br) OR from:(mercadopago.com))",
    "Microsoft": (
        "(from:(microsoft.com) OR "
        "from:(accountprotection.microsoft.com) OR "
        "from:(communication.microsoft.com) OR "
        "from:(notice.microsoft.com) OR "
        "from:(notificationemails.microsoft.com) OR "
        "from:(infomail.microsoft.com) OR "
        "from:(notificationmail.microsoft.com) OR "
        "from:(onedrive.com) OR "
        "from:(xbox.com))"
    ),
    "Motorola": "(from:(motorola-mail.com) OR from:(motorola.com))",
    "Netflix": "from:(netflix.com)",
    "Notion": "from:(notion.so)",
    "Nubank": "from:(nubank.com.br)",
    "Pinterest": "from:(pinterest.com)",
    "Samsung": "(from:(samsung.com) OR from:(samsung-mail.com))",
    "Santander": "(from:(santander.com.br) OR from:(santanderopenacademy.com))",
    "Shopee": "from:(shopee.com.br)",
    "Spotify": "from:(spotify.com)",
    "Truedata": (
        "(from:(truedata.com.br) OR "
        "from:(noreply@merchantsupport.io) OR "
        "from:(requests+truedata.com.br@judge.me))"
    ),
    "Uber": "from:(uber.com)",
    "YouCine": (
        "(from:(em3451.thetl1.com) OR "
        "from:(markmail.irmoal.com) OR "
        "subject:(YouCine))"
    ),
    "YouTube": "from:(youtube.com)",
}


def normalize_cnpj(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    return digits if len(digits) == 14 else ""


def format_cnpj(cnpj_digits: str) -> str:
    if len(cnpj_digits) != 14:
        return ""
    return (
        f"{cnpj_digits[0:2]}.{cnpj_digits[2:5]}.{cnpj_digits[5:8]}/"
        f"{cnpj_digits[8:12]}-{cnpj_digits[12:14]}"
    )


def format_cnpj_root(cnpj_digits: str) -> str:
    if len(cnpj_digits) != 14:
        return ""
    return f"{cnpj_digits[0:2]}.{cnpj_digits[2:5]}.{cnpj_digits[5:8]}"


def discover_mei_cnpj(service) -> str:
    # Descobre o CNPJ a partir de mensagens de um remetente MEI ja conhecido.
    # O numero fica somente em memoria e nunca e gravado no repositorio ou nos logs.
    response = (
        service.users()
        .messages()
        .list(
            userId="me",
            q="-in:trash -in:spam from:(meumeiassessoria.com.br)",
            maxResults=10,
        )
        .execute()
    )

    for item in response.get("messages", []):
        message = (
            service.users()
            .messages()
            .get(userId="me", id=item["id"], format="metadata")
            .execute()
        )
        snippet = message.get("snippet", "")
        for match in CNPJ_PATTERN.findall(snippet):
            digits = normalize_cnpj(match)
            if digits:
                return digits

    return ""


def get_auto_label_rules(service) -> Dict[str, str]:
    rules = dict(BASE_AUTO_LABEL_RULES)
    cnpj_digits = discover_mei_cnpj(service)

    if cnpj_digits:
        cnpj_formatted = format_cnpj(cnpj_digits)
        cnpj_root = format_cnpj_root(cnpj_digits)
        rules["MEI"] = (
            f'({rules["MEI"]} OR '
            f'"{cnpj_digits}" OR '
            f'"{cnpj_formatted}" OR '
            f'"{cnpj_root}")'
        )

    return rules


def load_credentials() -> Credentials:
    token_json = os.getenv("GMAIL_TOKEN_JSON", "").strip()
    if not token_json:
        raise RuntimeError("Secret GMAIL_TOKEN_JSON não configurado.")

    info = json.loads(token_json)
    return Credentials.from_authorized_user_info(info, SCOPES)


def get_label_map(service) -> Dict[str, str]:
    response = service.users().labels().list(userId="me").execute()
    return {label["name"]: label["id"] for label in response.get("labels", [])}


def list_matching_message_ids(service, query: str) -> List[str]:
    ids: List[str] = []
    page_token = None

    while True:
        response = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=500, pageToken=page_token)
            .execute()
        )
        ids.extend(message["id"] for message in response.get("messages", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return ids


def add_label_to_messages(service, message_ids: List[str], label_id: str, dry_run: bool) -> int:
    if not message_ids:
        return 0

    if dry_run:
        return len(message_ids)

    for start in range(0, len(message_ids), 1000):
        chunk = message_ids[start : start + 1000]
        (
            service.users()
            .messages()
            .batchModify(
                userId="me",
                body={"ids": chunk, "addLabelIds": [label_id]},
            )
            .execute()
        )

    return len(message_ids)


def archive_messages(service, message_ids: List[str], dry_run: bool) -> int:
    if not message_ids:
        return 0

    if dry_run:
        return len(message_ids)

    for start in range(0, len(message_ids), 1000):
        chunk = message_ids[start : start + 1000]
        (
            service.users()
            .messages()
            .batchModify(
                userId="me",
                body={"ids": chunk, "removeLabelIds": ["INBOX"]},
            )
            .execute()
        )

    return len(message_ids)


def main() -> int:
    dry_run = os.getenv("DRY_RUN", "false").lower() in {"1", "true", "yes", "on"}

    credentials = load_credentials()
    service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
    label_map = get_label_map(service)
    auto_label_rules = get_auto_label_rules(service)

    missing = [name for name in MONITORED_LABELS if name not in label_map]
    if missing:
        print("Marcadores ausentes no Gmail:", ", ".join(missing))

    labeled_total = 0
    for label_name, matching_query in auto_label_rules.items():
        label_id = label_map.get(label_name)
        if not label_id:
            continue

        # Corrige tambem mensagens antigas/arquivadas ainda sem o marcador.
        query = f'-in:trash -in:spam -label:"{label_name}" {matching_query}'
        message_ids = list_matching_message_ids(service, query)
        if not message_ids:
            continue

        count = add_label_to_messages(service, message_ids, label_id, dry_run=dry_run)
        labeled_total += count
        action = "receberiam o marcador" if dry_run else "receberam o marcador"
        print(f"{label_name}: {count} mensagem(ns) {action}.")

    archived_total = 0
    for label_name in MONITORED_LABELS:
        if label_name not in label_map:
            continue

        # Mantem nao lidas na Caixa de entrada. Quando forem lidas,
        # remove somente INBOX e preserva o marcador correspondente.
        query = f'in:inbox -is:unread label:"{label_name}"'
        message_ids = list_matching_message_ids(service, query)

        if not message_ids:
            continue

        count = archive_messages(service, message_ids, dry_run=dry_run)
        archived_total += count
        action = "seriam arquivadas" if dry_run else "arquivadas"
        print(f"{label_name}: {count} mensagem(ns) {action}.")

    mode = "DRY RUN" if dry_run else "EXECUÇÃO REAL"
    print(
        f"{mode}: marcadores aplicados = {labeled_total}; "
        f"mensagens arquivadas = {archived_total}."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise

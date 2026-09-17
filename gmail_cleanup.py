import json
import os
import sys
from typing import Dict, List

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

MONITORED_LABELS = [
    "99",
    "Âmbar",
    "Anhanguera",
    "Banco PAN",
    "ChatGPT",
    "Claro",
    "GitHub",
    "Google",
    "Gov",
    "IFAM",
    "Linkedin",
    "Mercado Livre",
    "Mercado Pago",
    "Motorola",
    "Netflix",
    "Nubank",
    "Shopee",
    "Uber",
]


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

    missing = [name for name in MONITORED_LABELS if name not in label_map]
    if missing:
        print("Marcadores ausentes no Gmail:", ", ".join(missing))

    total = 0
    for label_name in MONITORED_LABELS:
        if label_name not in label_map:
            continue

        # INBOX = ainda está na Caixa de entrada
        # -is:unread = já foi lida
        # label:"..." = pertence ao marcador correspondente
        query = f'in:inbox -is:unread label:"{label_name}"'
        message_ids = list_matching_message_ids(service, query)

        if not message_ids:
            continue

        count = archive_messages(service, message_ids, dry_run=dry_run)
        total += count
        action = "seriam arquivadas" if dry_run else "arquivadas"
        print(f"{label_name}: {count} mensagem(ns) {action}.")

    mode = "DRY RUN" if dry_run else "EXECUÇÃO REAL"
    print(f"{mode}: total processado = {total} mensagem(ns).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
LOOPBACK_HOST = "127.0.0.1"


def main() -> None:
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)

    credentials = flow.run_local_server(
        host=LOOPBACK_HOST,
        bind_addr=LOOPBACK_HOST,
        port=0,
        open_browser=True,
        authorization_prompt_message=(
            "Se o navegador nao abrir automaticamente, acesse esta URL:\n{url}\n"
        ),
        success_message=(
            "Autorizacao concluida com sucesso. Voce pode fechar esta janela e voltar ao terminal."
        ),
    )

    with open("token.json", "w", encoding="utf-8") as file:
        file.write(credentials.to_json())

    print("token.json criado com sucesso.")
    print("Copie TODO o conteudo desse arquivo para o secret GMAIL_TOKEN_JSON no GitHub.")


if __name__ == "__main__":
    main()

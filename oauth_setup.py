from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def main() -> None:
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    credentials = flow.run_local_server(port=0)

    with open("token.json", "w", encoding="utf-8") as file:
        file.write(credentials.to_json())

    print("token.json criado com sucesso.")
    print("Copie TODO o conteúdo desse arquivo para o secret GMAIL_TOKEN_JSON no GitHub.")


if __name__ == "__main__":
    main()

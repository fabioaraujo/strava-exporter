"""Script principal para importar atividades do Strava."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from strava_import.strava_api import StravaClient
from strava_import.markdown_exporter import activities_to_markdown, activities_to_markdown_by_type


def setup_credentials():
    """Configura e valida as credenciais do Strava."""
    load_dotenv()
    
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    access_token = os.getenv("STRAVA_ACCESS_TOKEN")
    
    if not client_id or not client_secret:
        print("❌ Credenciais não encontradas!")
        print("\nPara usar este script, você precisa:")
        print("1. Criar um aplicativo em: https://www.strava.com/settings/api")
        print("2. Criar um arquivo .env com:")
        print("   STRAVA_CLIENT_ID=seu_client_id")
        print("   STRAVA_CLIENT_SECRET=seu_client_secret")
        print("   STRAVA_ACCESS_TOKEN=seu_access_token (opcional)")
        sys.exit(1)
    
    return client_id, client_secret, access_token


def get_authorization():
    """Guia o usuário pelo processo de autorização."""
    client_id, client_secret, _ = setup_credentials()
    client = StravaClient(client_id, client_secret)
    
    print("\n🔐 Processo de Autorização OAuth2")
    print("=" * 50)
    auth_url = client.get_authorization_url()
    print(f"\n1. Abra este link no navegador:\n   {auth_url}")
    print("\n2. Autorize o aplicativo")
    print("3. Você será redirecionado para uma URL como:")
    print("   http://localhost/?state=&code=CODIGO_AQUI&scope=...")
    print("\n4. Copie o CÓDIGO da URL (parte depois de 'code=')")
    
    code = input("\n📋 Cole o código aqui: ").strip()
    
    if not code:
        print("❌ Código inválido!")
        sys.exit(1)
    
    print("\n⏳ Trocando código por token...")
    try:
        token_data = client.exchange_token(code)
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token", "")
        
        print("\n✅ Token obtido com sucesso!")
        print("\n📝 Adicione estas linhas ao seu arquivo .env:")
        print(f"   STRAVA_ACCESS_TOKEN={access_token}")
        if refresh_token:
            print(f"   STRAVA_REFRESH_TOKEN={refresh_token}")
        
        return access_token
    except Exception as e:
        print(f"\n❌ Erro ao obter token: {e}")
        sys.exit(1)


def main():
    """Função principal."""
    print("🚴 Strava Import - Importador de Atividades")
    print("=" * 50)
    
    # Verificar se há token
    client_id, client_secret, access_token = setup_credentials()
    
    if not access_token:
        print("\n⚠️  Access token não encontrado.")
        response = input("Deseja iniciar o processo de autorização? (s/n): ").lower()
        
        if response == 's':
            access_token = get_authorization()
        else:
            print("\n❌ Não é possível continuar sem access token.")
            sys.exit(1)
    
    # Criar cliente
    client = StravaClient(client_id, client_secret, access_token)
    
    try:
        # Obter informações do atleta
        print("\n⏳ Obtendo informações do atleta...")
        athlete = client.get_athlete()
        print(f"✅ Conectado como: {athlete['firstname']} {athlete['lastname']}")
        
        # Buscar atividades
        print("\n⏳ Buscando atividades...")
        print("   (Isso pode levar alguns minutos para muitas atividades...)")
        activities = client.get_all_activities()  # Buscar todas as atividades
        print(f"✅ {len(activities)} atividades encontradas")
        
        if not activities:
            print("\n⚠️  Nenhuma atividade encontrada.")
            return
        
        # Exportar para markdown
        print("\n⏳ Exportando para Markdown...")
        
        # Arquivo geral
        output_file = activities_to_markdown(activities)
        print(f"✅ Arquivo criado: {output_file}")
        
        # Arquivo por tipo
        output_file_by_type = activities_to_markdown_by_type(activities)
        print(f"✅ Arquivo criado: {output_file_by_type}")
        
        print("\n🎉 Importação concluída com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

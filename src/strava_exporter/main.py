"""Script principal para exportar atividades do Strava."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from strava_exporter.strava_api import StravaClient
from strava_exporter.markdown_exporter import activities_to_markdown_by_year
from strava_exporter.cache import (
    load_cache,
    save_cache,
    merge_activities,
    get_new_activities_count
)


def update_env_tokens(access_token: str, refresh_token: str):
    """
    Atualiza os tokens no arquivo .env.
    
    Args:
        access_token: Novo access token
        refresh_token: Novo refresh token
    """
    env_path = Path(".env")
    
    if not env_path.exists():
        return
    
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        with open(env_path, "w", encoding="utf-8") as f:
            for line in lines:
                if line.startswith("STRAVA_ACCESS_TOKEN="):
                    f.write(f"STRAVA_ACCESS_TOKEN={access_token}\n")
                elif line.startswith("STRAVA_REFRESH_TOKEN="):
                    f.write(f"STRAVA_REFRESH_TOKEN={refresh_token}\n")
                else:
                    f.write(line)
        
        print("💾 Tokens atualizados no arquivo .env")
    except Exception as e:
        print(f"⚠️  Erro ao atualizar .env: {e}")


def setup_credentials():
    """Configura e valida as credenciais do Strava."""
    load_dotenv()
    
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    access_token = os.getenv("STRAVA_ACCESS_TOKEN")
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
    
    if not client_id or not client_secret:
        print("❌ Credenciais não encontradas!")
        print("\nPara usar este script, você precisa:")
        print("1. Criar um aplicativo em: https://www.strava.com/settings/api")
        print("2. Criar um arquivo .env com:")
        print("   STRAVA_CLIENT_ID=seu_client_id")
        print("   STRAVA_CLIENT_SECRET=seu_client_secret")
        print("   STRAVA_ACCESS_TOKEN=seu_access_token (opcional)")
        print("   STRAVA_REFRESH_TOKEN=seu_refresh_token (opcional)")
        sys.exit(1)
    
    return client_id, client_secret, access_token, refresh_token


def get_authorization():
    """Guia o usuário pelo processo de autorização."""
    client_id, client_secret, _, _ = setup_credentials()
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
        
        return access_token, refresh_token
    except Exception as e:
        print(f"\n❌ Erro ao obter token: {e}")
        sys.exit(1)


def main():
    """Função principal."""
    print("🚴 Strava Exporter - Exportador de Atividades")
    print("=" * 50)
    
    # Verificar se há token
    client_id, client_secret, access_token, refresh_token = setup_credentials()
    
    if not access_token:
        print("\n⚠️  Access token não encontrado.")
        response = input("Deseja iniciar o processo de autorização? (s/n): ").lower()
        
        if response == 's':
            access_token, refresh_token = get_authorization()
        else:
            print("\n❌ Não é possível continuar sem access token.")
            sys.exit(1)
    
    # Criar cliente com callback para salvar tokens
    client = StravaClient(
        client_id, 
        client_secret, 
        access_token, 
        refresh_token,
        token_update_callback=update_env_tokens
    )
    
    try:
        # Obter informações do atleta
        print("\n⏳ Obtendo informações do atleta...")
        athlete = client.get_athlete()
        print(f"✅ Conectado como: {athlete['firstname']} {athlete['lastname']}")
        
        # Carregar cache
        print("\n⏳ Verificando cache local...")
        cache = load_cache()
        cached_activities = cache.get("activities", [])
        
        if cached_activities:
            print(f"💾 {len(cached_activities)} atividades no cache")
            last_update = cache.get("last_update", "desconhecida")
            print(f"   Última atualização: {last_update}")
            
            # Perguntar se quer atualizar
            response = input("\nDeseja buscar novas atividades? (s/n): ").lower()
            
            if response != 's':
                print("\n📊 Usando atividades do cache...")
                activities = cached_activities
            else:
                # Buscar apenas atividades recentes (última página)
                print("\n⏳ Buscando novas atividades...")
                new_activities = client.get_activities(per_page=200, page=1)
                
                # Mesclar com cache
                activities = merge_activities(cached_activities, new_activities)
                new_count = get_new_activities_count(cached_activities, activities)
                
                if new_count > 0:
                    print(f"✅ {new_count} nova(s) atividade(s) encontrada(s)")
                    save_cache(activities)
                else:
                    print(f"✅ Nenhuma atividade nova")
        else:
            print("📥 Nenhum cache encontrado. Buscando todas as atividades...")
            print("   (Isso pode levar alguns minutos para muitas atividades...)")
            
            # Buscar todas as atividades
            activities = client.get_all_activities()
            print(f"✅ {len(activities)} atividades encontradas")
            
            # Salvar no cache
            save_cache(activities)
        
        if not activities:
            print("\n⚠️  Nenhuma atividade encontrada.")
            return
        
        # Exportar para markdown
        print(f"\n⏳ Exportando {len(activities)} atividades para Markdown...")
        
        # Arquivos por ano
        files_by_year = activities_to_markdown_by_year(activities)
        print(f"✅ {len(files_by_year)} arquivos gerados no diretório 'atividades/'")
        
        print("\n🎉 Exportação concluída com sucesso!")
        print(f"\n📖 Veja o índice em: atividades/README.md")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

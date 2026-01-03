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
            
            # Mostrar FC máxima do cache se disponível
            cached_max_hr = cache.get("detected_max_hr")
            cached_max_hr_date = cache.get("detected_max_hr_date")
            if cached_max_hr:
                year = cached_max_hr_date[:4] if cached_max_hr_date else "?"
                print(f"   💓 FC Máxima no cache: {int(cached_max_hr)} bpm (de {year})")
            
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
                    
                    # Buscar detalhes das novas atividades
                    print(f"⏳ Buscando detalhes das {new_count} novas atividades...")
                    for i, activity in enumerate(activities[:new_count], 1):
                        if not activity.get("_detailed"):  # Verifica se já tem detalhes
                            try:
                                activity_id = activity["id"]
                                details = client.get_activity_details(activity_id)
                                
                                # Adicionar campos detalhados à atividade
                                activity["suffer_score"] = details.get("suffer_score")
                                activity["calories"] = details.get("calories")
                                activity["average_watts"] = details.get("average_watts")
                                activity["max_watts"] = details.get("max_watts")
                                activity["weighted_average_watts"] = details.get("weighted_average_watts")
                                activity["device_watts"] = details.get("device_watts", False)
                                activity["kilojoules"] = details.get("kilojoules")
                                activity["_detailed"] = True
                                
                                print(f"   [{i}/{new_count}] {activity.get('name', 'N/A')}")
                                
                                # Salvar cache a cada 10 atividades
                                if i % 10 == 0:
                                    save_cache(activities)
                                    print(f"   💾 Cache salvo ({i}/{new_count})")
                            except KeyboardInterrupt:
                                print("\n⏸️  Interrompido pelo usuário. Salvando progresso...")
                                save_cache(activities)
                                print("✅ Progresso salvo! Execute novamente para continuar.")
                                return
                            except Exception as e:
                                print(f"   ⚠️  Erro ao buscar detalhes da atividade {activity_id}: {e}")
                                # Salvar cache mesmo em caso de erro
                                save_cache(activities)
                    
                    save_cache(activities)
                else:
                    print(f"✅ Nenhuma atividade nova")
        else:
            print("📥 Nenhum cache encontrado. Buscando todas as atividades...")
            print("   (Isso pode levar alguns minutos para muitas atividades...)")
            
            # Buscar todas as atividades
            activities = client.get_all_activities()
            print(f"✅ {len(activities)} atividades encontradas")
            
            # Perguntar se quer buscar detalhes
            response = input("\n⚠️  Buscar detalhes completos de todas as atividades?\n   (Recomendado: não, busque apenas para atividades novas depois)\n   (s/n): ").lower()
            
            if response == 's':
                # Verificar quantas já têm detalhes
                pending = [a for a in activities if not a.get("_detailed")]
                completed = len(activities) - len(pending)
                
                if completed > 0:
                    print(f"\n✅ {completed} atividades já processadas anteriormente")
                    print(f"⏳ Buscando detalhes de {len(pending)} atividades restantes...")
                else:
                    print(f"\n⏳ Buscando detalhes de {len(activities)} atividades...")
                
                print("   (Isso levará vários minutos...)")
                print("   💡 Pressione Ctrl+C para pausar e salvar progresso\n")
                
                for i, activity in enumerate(pending, 1):
                    try:
                        activity_id = activity["id"]
                        details = client.get_activity_details(activity_id)
                        
                        # Adicionar campos detalhados
                        activity["suffer_score"] = details.get("suffer_score")
                        activity["calories"] = details.get("calories")
                        activity["average_watts"] = details.get("average_watts")
                        activity["max_watts"] = details.get("max_watts")
                        activity["weighted_average_watts"] = details.get("weighted_average_watts")
                        activity["device_watts"] = details.get("device_watts", False)
                        activity["kilojoules"] = details.get("kilojoules")
                        activity["_detailed"] = True
                        
                        if i % 50 == 0:
                            print(f"   Processadas {i}/{len(pending)} atividades...")
                            save_cache(activities)
                            print(f"   💾 Cache salvo ({completed + i}/{len(activities)})")
                    except KeyboardInterrupt:
                        print("\n⏸️  Interrompido pelo usuário. Salvando progresso...")
                        save_cache(activities)
                        completed_now = completed + i
                        print(f"✅ Progresso salvo! {completed_now}/{len(activities)} atividades processadas.")
                        print(f"   Execute novamente para continuar com as {len(activities) - completed_now} restantes.")
                        return
                    except Exception as e:
                        print(f"   ⚠️  Erro na atividade {activity_id}: {e}")
                        # Salvar cache a cada erro também
                        if i % 10 == 0:
                            save_cache(activities)
                
                print(f"✅ Detalhes obtidos para todas as {len(activities)} atividades")
            
            # Salvar no cache
            save_cache(activities)
        
        if not activities:
            print("\n⚠️  Nenhuma atividade encontrada.")
            return
        
        # Obter FC máxima do usuário do .env (opcional)
        user_max_hr = os.getenv("USER_MAX_HR")
        if user_max_hr:
            try:
                user_max_hr = float(user_max_hr)
                print(f"\n💓 Usando FC Máxima configurada: {int(user_max_hr)} bpm (do arquivo .env)")
            except ValueError:
                user_max_hr = None
        else:
            # Verificar se FC do cache precisa ser atualizada
            cached_max_hr = cache.get("detected_max_hr")
            cached_max_hr_date = cache.get("detected_max_hr_date")
            
            needs_update = False
            if cached_max_hr and cached_max_hr_date:
                # Verificar se a FC do cache tem mais de 6 meses
                from datetime import datetime, timedelta
                cache_date = datetime.fromisoformat(cached_max_hr_date.replace("Z", "+00:00"))
                age_days = (datetime.now(cache_date.tzinfo) - cache_date).days
                
                if age_days > 180:  # 6 meses
                    print(f"\n⚠️  FC Máxima do cache tem {age_days} dias ({age_days // 30} meses)")
                    print(f"   Recalculando com base nos dados recentes...")
                    needs_update = True
                else:
                    user_max_hr = cached_max_hr
                    print(f"\n💓 Usando FC Máxima do cache: {int(user_max_hr)} bpm")
                    print(f"   Última detecção: há {age_days} dias")
            else:
                needs_update = True
            
            # Se precisa atualizar, será recalculado no markdown_exporter
            if needs_update:
                user_max_hr = None  # Força recálculo
        
        # Exportar para markdown
        print(f"\n⏳ Exportando {len(activities)} atividades para Markdown...")
        
        # Arquivos por ano (recalcula FC se user_max_hr = None)
        files_by_year, new_detected_hr, new_detection_date = activities_to_markdown_by_year(activities, user_max_hr=user_max_hr)
        
        # Se uma nova FC foi detectada, salvar no cache
        if new_detected_hr and new_detection_date:
            cache["detected_max_hr"] = new_detected_hr
            cache["detected_max_hr_date"] = new_detection_date
            save_cache(activities)
            print(f"   💾 FC Máxima salva no cache: {int(new_detected_hr)} bpm")
        
        print(f"✅ {len(files_by_year)} arquivos gerados no diretório 'atividades/'")
        
        print("\n🎉 Exportação concluída com sucesso!")
        print(f"\n📖 Veja o índice em: atividades/README.md")
        print(f"📊 Estatísticas anuais: atividades/estatisticas_anuais.md")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

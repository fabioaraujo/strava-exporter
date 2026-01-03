"""Módulo para autenticação e interação com a API do Strava."""

import time
import requests
from typing import Optional, Dict, Any, Callable


class StravaClient:
    """Cliente para interagir com a API do Strava."""
    
    BASE_URL = "https://www.strava.com/api/v3"
    AUTH_URL = "https://www.strava.com/oauth/authorize"
    TOKEN_URL = "https://www.strava.com/oauth/token"
    
    def __init__(self, client_id: str, client_secret: str, access_token: Optional[str] = None, 
                 refresh_token: Optional[str] = None, token_update_callback: Optional[Callable] = None):
        """
        Inicializa o cliente Strava.
        
        Args:
            client_id: ID do aplicativo Strava
            client_secret: Secret do aplicativo Strava
            access_token: Token de acesso (opcional, se já tiver um)
            refresh_token: Refresh token (opcional, para renovação automática)
            token_update_callback: Função callback para salvar tokens atualizados
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_update_callback = token_update_callback
    
    def get_authorization_url(self, redirect_uri: str = "http://localhost", scope: str = "read,activity:read_all") -> str:
        """
        Gera URL para autorização OAuth2.
        
        Args:
            redirect_uri: URI de redirecionamento
            scope: Escopos de permissão
            
        Returns:
            URL de autorização
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
        }
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTH_URL}?{query}"
    
    def exchange_token(self, code: str) -> Dict[str, Any]:
        """
        Troca o código de autorização por um token de acesso.
        
        Args:
            code: Código de autorização recebido
            
        Returns:
            Resposta com tokens
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data["access_token"]
        return token_data
    
    def refresh_access_token(self, refresh_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Atualiza o token de acesso usando refresh token.
        
        Args:
            refresh_token: Refresh token (usa o armazenado se não fornecido)
            
        Returns:
            Resposta com novos tokens
        """
        token_to_use = refresh_token or self.refresh_token
        
        if not token_to_use:
            raise ValueError("Refresh token não disponível")
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": token_to_use,
            "grant_type": "refresh_token",
        }
        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        # Atualizar tokens
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token", self.refresh_token)
        
        # Chamar callback se fornecido
        if self.token_update_callback:
            self.token_update_callback(self.access_token, self.refresh_token)
        
        return token_data
    
    def _make_request(self, method: str, endpoint: str, max_retries: int = 5, **kwargs) -> requests.Response:
        """
        Faz uma requisição HTTP com renovação automática de token e retry em caso de rate limit.
        
        Args:
            method: Método HTTP (get, post, etc)
            endpoint: Endpoint da API
            max_retries: Número máximo de tentativas em caso de 429
            **kwargs: Argumentos adicionais para requests
            
        Returns:
            Response object
        """
        if not self.access_token:
            raise ValueError("Access token não configurado")
        
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        
        for attempt in range(max_retries):
            response = requests.request(method, f"{self.BASE_URL}/{endpoint}", headers=headers, **kwargs)
            
            # Se receber 401, tentar renovar o token
            if response.status_code == 401 and self.refresh_token:
                print("🔄 Token expirado, renovando automaticamente...")
                try:
                    self.refresh_access_token()
                    # Tentar novamente com o novo token
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    response = requests.request(method, f"{self.BASE_URL}/{endpoint}", headers=headers, **kwargs)
                    print("✅ Token renovado com sucesso!")
                except Exception as e:
                    print(f"❌ Erro ao renovar token: {e}")
                    raise
            
            # Se receber 429 (Rate Limit), aguardar e tentar novamente
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 15 * 60))  # Default 15 min
                wait_time = min(retry_after, 15 * 60)  # Máximo 15 minutos
                
                if attempt < max_retries - 1:
                    print(f"⏸️  Rate limit atingido! Aguardando {wait_time}s antes de tentar novamente...")
                    print(f"   (Tentativa {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Rate limit atingido após {max_retries} tentativas")
                    raise requests.exceptions.HTTPError(f"429 Rate Limit Exceeded after {max_retries} retries", response=response)
            
            # Para qualquer outro erro, lançar exceção
            response.raise_for_status()
            return response
        
        # Se chegou aqui, todas as tentativas falharam
        response.raise_for_status()
        return response
    
    def get_athlete(self) -> Dict[str, Any]:
        """
        Obtém informações do atleta autenticado.
        
        Returns:
            Dados do atleta
        """
        response = self._make_request("get", "athlete")
        return response.json()
    
    def get_activities(self, per_page: int = 30, page: int = 1) -> list[Dict[str, Any]]:
        """
        Obtém atividades do atleta.
        
        Args:
            per_page: Número de atividades por página (máx 200)
            page: Número da página
            
        Returns:
            Lista de atividades
        """
        params = {"per_page": per_page, "page": page}
        response = self._make_request("get", "athlete/activities", params=params)
        return response.json()
    
    def get_all_activities(self, max_activities: Optional[int] = None) -> list[Dict[str, Any]]:
        """
        Obtém todas as atividades do atleta (paginação automática).
        
        Args:
            max_activities: Número máximo de atividades para buscar
            
        Returns:
            Lista completa de atividades
        """
        all_activities = []
        page = 1
        per_page = 200  # Máximo permitido pela API
        
        while True:
            activities = self.get_activities(per_page=per_page, page=page)
            
            if not activities:
                break
            
            all_activities.extend(activities)
            
            if max_activities and len(all_activities) >= max_activities:
                all_activities = all_activities[:max_activities]
                break
            
            if len(activities) < per_page:
                break
            
            page += 1
        
        return all_activities
    
    def get_activity_details(self, activity_id: int) -> Dict[str, Any]:
        """
        Obtém detalhes completos de uma atividade específica.
        Inclui métricas adicionais como suffer_score, calories, watts, etc.
        
        Args:
            activity_id: ID da atividade
            
        Returns:
            Dados detalhados da atividade
        """
        response = self._make_request("get", f"activities/{activity_id}")
        return response.json()

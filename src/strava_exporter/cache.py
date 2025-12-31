"""Módulo para cache de atividades do Strava."""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


CACHE_FILE = "strava_cache.json"


def load_cache() -> Dict[str, Any]:
    """
    Carrega o cache de atividades.
    
    Returns:
        Dicionário com atividades e metadados
    """
    cache_path = Path(CACHE_FILE)
    
    if not cache_path.exists():
        return {
            "last_update": None,
            "activities": []
        }
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Erro ao ler cache: {e}")
        return {
            "last_update": None,
            "activities": []
        }


def save_cache(activities: List[Dict[str, Any]]) -> None:
    """
    Salva atividades no cache.
    
    Args:
        activities: Lista de atividades para salvar
    """
    cache_data = {
        "last_update": datetime.now().isoformat(),
        "total_activities": len(activities),
        "activities": activities
    }
    
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Cache salvo: {len(activities)} atividades")
    except Exception as e:
        print(f"⚠️  Erro ao salvar cache: {e}")


def merge_activities(cached: List[Dict[str, Any]], new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Mescla atividades do cache com novas atividades.
    Remove duplicatas baseado no ID.
    
    Args:
        cached: Atividades do cache
        new: Novas atividades da API
        
    Returns:
        Lista mesclada sem duplicatas, ordenada por data (mais recente primeiro)
    """
    # Criar dicionário com IDs das atividades
    activities_dict = {}
    
    # Adicionar atividades do cache
    for activity in cached:
        activity_id = activity.get("id")
        if activity_id:
            activities_dict[activity_id] = activity
    
    # Adicionar/atualizar com novas atividades
    for activity in new:
        activity_id = activity.get("id")
        if activity_id:
            activities_dict[activity_id] = activity
    
    # Converter de volta para lista e ordenar por data
    merged = list(activities_dict.values())
    merged.sort(key=lambda x: x.get("start_date", ""), reverse=True)
    
    return merged


def get_new_activities_count(cached: List[Dict[str, Any]], merged: List[Dict[str, Any]]) -> int:
    """
    Calcula quantas atividades novas foram adicionadas.
    
    Args:
        cached: Atividades anteriores
        merged: Atividades após merge
        
    Returns:
        Número de atividades novas
    """
    return len(merged) - len(cached)

"""Módulo para exportar atividades do Strava para formato Markdown."""

from datetime import datetime
from typing import List, Dict, Any


def format_distance(meters: float) -> str:
    """Converte metros para km formatado."""
    return f"{meters / 1000:.2f} km"


def format_duration(seconds: int) -> str:
    """Converte segundos para formato HH:MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_pace(meters: float, seconds: int) -> str:
    """Calcula e formata o pace (min/km)."""
    if meters == 0:
        return "N/A"
    
    km = meters / 1000
    pace_seconds = seconds / km
    pace_minutes = int(pace_seconds // 60)
    pace_secs = int(pace_seconds % 60)
    
    return f"{pace_minutes}:{pace_secs:02d} /km"


def format_date(date_str: str) -> str:
    """Formata a data da atividade."""
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return dt.strftime("%d/%m/%Y %H:%M")


def activities_to_markdown(activities: List[Dict[str, Any]], output_file: str = "strava_activities.md") -> str:
    """
    Converte lista de atividades para formato Markdown tabular.
    
    Args:
        activities: Lista de atividades do Strava
        output_file: Nome do arquivo de saída
        
    Returns:
        Caminho do arquivo criado
    """
    # Cabeçalho do documento
    markdown = "# Atividades do Strava\n\n"
    markdown += f"**Total de atividades:** {len(activities)}\n\n"
    
    # Estatísticas gerais
    total_distance = sum(a.get("distance", 0) for a in activities)
    total_time = sum(a.get("moving_time", 0) for a in activities)
    
    markdown += "## Estatísticas Gerais\n\n"
    markdown += f"- **Distância total:** {format_distance(total_distance)}\n"
    markdown += f"- **Tempo total:** {format_duration(total_time)}\n"
    markdown += f"- **Média por atividade:** {format_distance(total_distance / len(activities) if activities else 0)}\n\n"
    
    # Tabela de atividades
    markdown += "## Tabela de Atividades\n\n"
    markdown += "| Data | Nome | Tipo | Distância | Duração | Pace | Elevação | Kudos |\n"
    markdown += "|------|------|------|-----------|---------|------|----------|-------|\n"
    
    for activity in activities:
        name = activity.get("name", "N/A")
        sport_type = activity.get("sport_type", activity.get("type", "N/A"))
        distance = activity.get("distance", 0)
        moving_time = activity.get("moving_time", 0)
        date = activity.get("start_date", "N/A")
        elevation = activity.get("total_elevation_gain", 0)
        kudos = activity.get("kudos_count", 0)
        
        # Formatar dados
        date_formatted = format_date(date) if date != "N/A" else "N/A"
        distance_formatted = format_distance(distance)
        duration_formatted = format_duration(moving_time)
        pace_formatted = format_pace(distance, moving_time) if distance > 0 else "N/A"
        elevation_formatted = f"{elevation:.0f} m"
        
        markdown += f"| {date_formatted} | {name} | {sport_type} | {distance_formatted} | {duration_formatted} | {pace_formatted} | {elevation_formatted} | {kudos} |\n"
    
    # Salvar arquivo
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    return output_file


def activities_to_markdown_by_type(activities: List[Dict[str, Any]], output_file: str = "strava_by_type.md") -> str:
    """
    Converte lista de atividades para formato Markdown agrupado por tipo.
    
    Args:
        activities: Lista de atividades do Strava
        output_file: Nome do arquivo de saída
        
    Returns:
        Caminho do arquivo criado
    """
    # Agrupar por tipo
    activities_by_type: Dict[str, List[Dict[str, Any]]] = {}
    
    for activity in activities:
        sport_type = activity.get("sport_type", activity.get("type", "Outro"))
        if sport_type not in activities_by_type:
            activities_by_type[sport_type] = []
        activities_by_type[sport_type].append(activity)
    
    # Cabeçalho do documento
    markdown = "# Atividades do Strava por Tipo\n\n"
    markdown += f"**Total de atividades:** {len(activities)}\n"
    markdown += f"**Tipos de atividade:** {len(activities_by_type)}\n\n"
    
    # Para cada tipo
    for sport_type, type_activities in sorted(activities_by_type.items()):
        total_distance = sum(a.get("distance", 0) for a in type_activities)
        total_time = sum(a.get("moving_time", 0) for a in type_activities)
        
        markdown += f"## {sport_type}\n\n"
        markdown += f"**Total:** {len(type_activities)} atividades | "
        markdown += f"**Distância:** {format_distance(total_distance)} | "
        markdown += f"**Tempo:** {format_duration(total_time)}\n\n"
        
        markdown += "| Data | Nome | Distância | Duração | Pace | Elevação |\n"
        markdown += "|------|------|-----------|---------|------|----------|\n"
        
        for activity in type_activities:
            name = activity.get("name", "N/A")
            distance = activity.get("distance", 0)
            moving_time = activity.get("moving_time", 0)
            date = activity.get("start_date", "N/A")
            elevation = activity.get("total_elevation_gain", 0)
            
            date_formatted = format_date(date) if date != "N/A" else "N/A"
            distance_formatted = format_distance(distance)
            duration_formatted = format_duration(moving_time)
            pace_formatted = format_pace(distance, moving_time) if distance > 0 else "N/A"
            elevation_formatted = f"{elevation:.0f} m"
            
            markdown += f"| {date_formatted} | {name} | {distance_formatted} | {duration_formatted} | {pace_formatted} | {elevation_formatted} |\n"
        
        markdown += "\n"
    
    # Salvar arquivo
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    return output_file

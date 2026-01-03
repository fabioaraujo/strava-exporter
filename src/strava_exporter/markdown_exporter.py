"""Módulo para exportar atividades do Strava para formato Markdown."""

from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from collections import defaultdict


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


def calculate_pace_seconds(meters: float, seconds: int) -> float:
    """Calcula o pace em segundos por km."""
    if meters == 0:
        return float('inf')
    km = meters / 1000
    return seconds / km


def calculate_records(activities: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Calcula recordes pessoais por tipo de atividade.
    
    Args:
        activities: Lista de atividades
        
    Returns:
        Dicionário com recordes por tipo de atividade
    """
    records_by_type: Dict[str, Dict[str, Any]] = {}
    
    for activity in activities:
        sport_type = activity.get("sport_type", activity.get("type", "Outro"))
        distance = activity.get("distance", 0)
        moving_time = activity.get("moving_time", 0)
        elevation = activity.get("total_elevation_gain", 0)
        
        if sport_type not in records_by_type:
            records_by_type[sport_type] = {
                "max_distance": {"value": 0, "activity": None},
                "max_time": {"value": 0, "activity": None},
                "max_elevation": {"value": 0, "activity": None},
                "best_pace": {"value": float('inf'), "activity": None},
            }
        
        records = records_by_type[sport_type]
        
        # Maior distância
        if distance > records["max_distance"]["value"]:
            records["max_distance"]["value"] = distance
            records["max_distance"]["activity"] = activity
        
        # Maior tempo
        if moving_time > records["max_time"]["value"]:
            records["max_time"]["value"] = moving_time
            records["max_time"]["activity"] = activity
        
        # Maior elevação
        if elevation > records["max_elevation"]["value"]:
            records["max_elevation"]["value"] = elevation
            records["max_elevation"]["activity"] = activity
        
        # Melhor pace (apenas para atividades com distância)
        if distance > 0:
            pace = calculate_pace_seconds(distance, moving_time)
            if pace < records["best_pace"]["value"]:
                records["best_pace"]["value"] = pace
                records["best_pace"]["activity"] = activity
    
    return records_by_type


def format_records_markdown(records_by_type: Dict[str, Dict[str, Any]], title: str = "Recordes Pessoais") -> str:
    """
    Formata recordes em markdown.
    
    Args:
        records_by_type: Dicionário de recordes por tipo
        title: Título da seção
        
    Returns:
        String markdown formatada
    """
    if not records_by_type:
        return ""
    
    markdown = f"## {title}\n\n"
    
    for sport_type in sorted(records_by_type.keys()):
        records = records_by_type[sport_type]
        markdown += f"### {sport_type}\n\n"
        
        # Maior distância
        if records["max_distance"]["activity"]:
            act = records["max_distance"]["activity"]
            markdown += f"- **Maior Distância:** {format_distance(act.get('distance', 0))}"
            markdown += f" - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})\n"
        
        # Maior tempo
        if records["max_time"]["activity"]:
            act = records["max_time"]["activity"]
            markdown += f"- **Maior Tempo:** {format_duration(act.get('moving_time', 0))}"
            markdown += f" - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})\n"
        
        # Maior elevação
        if records["max_elevation"]["activity"]:
            act = records["max_elevation"]["activity"]
            elev = act.get('total_elevation_gain', 0)
            if elev > 0:
                markdown += f"- **Maior Elevação:** {elev:.0f} m"
                markdown += f" - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})\n"
        
        # Melhor pace (se aplicável)
        if records["best_pace"]["activity"] and records["best_pace"]["value"] != float('inf'):
            act = records["best_pace"]["activity"]
            distance = act.get('distance', 0)
            moving_time = act.get('moving_time', 0)
            if distance > 0:
                pace = format_pace(distance, moving_time)
                markdown += f"- **Melhor Pace:** {pace}"
                markdown += f" - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})\n"
        
        markdown += "\n"
    
    return markdown


def format_records_comparison(year_records: Dict[str, Dict[str, Any]], all_time_records: Dict[str, Dict[str, Any]], year: int) -> str:
    """
    Formata recordes em formato de tabela comparativa.
    
    Args:
        year_records: Recordes do ano
        all_time_records: Recordes de todos os tempos
        year: Ano dos recordes
        
    Returns:
        String markdown formatada
    """
    if not year_records and not all_time_records:
        return ""
    
    markdown = f"## Recordes Pessoais\n\n"
    
    # Obter todos os tipos de atividade (do ano e gerais)
    all_types = set(year_records.keys()) | set(all_time_records.keys())
    
    for sport_type in sorted(all_types):
        markdown += f"### {sport_type}\n\n"
        markdown += "| Métrica | Recorde de {0} | Recorde Geral (até {0}) |\n".format(year)
        markdown += "|---------|----------------|------------------------|\n"
        
        year_rec = year_records.get(sport_type, {})
        all_rec = all_time_records.get(sport_type, {})
        
        # Maior distância
        year_dist = ""
        if year_rec.get("max_distance", {}).get("activity"):
            act = year_rec["max_distance"]["activity"]
            year_dist = f"{format_distance(act.get('distance', 0))} - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})"
        
        all_dist = ""
        if all_rec.get("max_distance", {}).get("activity"):
            act = all_rec["max_distance"]["activity"]
            all_dist = f"{format_distance(act.get('distance', 0))} - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})"
        
        if year_dist or all_dist:
            markdown += f"| **Maior Distância** | {year_dist or 'N/A'} | {all_dist or 'N/A'} |\n"
        
        # Maior tempo
        year_time = ""
        if year_rec.get("max_time", {}).get("activity"):
            act = year_rec["max_time"]["activity"]
            year_time = f"{format_duration(act.get('moving_time', 0))} - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})"
        
        all_time = ""
        if all_rec.get("max_time", {}).get("activity"):
            act = all_rec["max_time"]["activity"]
            all_time = f"{format_duration(act.get('moving_time', 0))} - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})"
        
        if year_time or all_time:
            markdown += f"| **Maior Tempo** | {year_time or 'N/A'} | {all_time or 'N/A'} |\n"
        
        # Maior elevação
        year_elev = ""
        if year_rec.get("max_elevation", {}).get("activity"):
            act = year_rec["max_elevation"]["activity"]
            elev = act.get('total_elevation_gain', 0)
            if elev > 0:
                year_elev = f"{elev:.0f} m - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})"
        
        all_elev = ""
        if all_rec.get("max_elevation", {}).get("activity"):
            act = all_rec["max_elevation"]["activity"]
            elev = act.get('total_elevation_gain', 0)
            if elev > 0:
                all_elev = f"{elev:.0f} m - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})"
        
        if year_elev or all_elev:
            markdown += f"| **Maior Elevação** | {year_elev or 'N/A'} | {all_elev or 'N/A'} |\n"
        
        markdown += "\n"
    
    return markdown


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


def get_year_from_activity(activity: Dict[str, Any]) -> int:
    """
    Extrai o ano de uma atividade.
    
    Args:
        activity: Atividade do Strava
        
    Returns:
        Ano da atividade
    """
    date_str = activity.get("start_date", "")
    if date_str:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.year
    return 0


def activities_to_markdown_by_year(activities: List[Dict[str, Any]], output_dir: str = "atividades") -> List[str]:
    """
    Converte lista de atividades para formato Markdown separado por ano.
    
    Args:
        activities: Lista de atividades do Strava
        output_dir: Diretório para salvar os arquivos
        
    Returns:
        Lista de caminhos dos arquivos criados
    """
    # Criar diretório se não existir
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Agrupar atividades por ano
    activities_by_year: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    
    for activity in activities:
        year = get_year_from_activity(activity)
        if year > 0:
            activities_by_year[year].append(activity)
    
    created_files = []
    
    # Gerar arquivo para cada ano
    for year in sorted(activities_by_year.keys(), reverse=True):
        year_activities = activities_by_year[year]
        
        # Calcular estatísticas do ano
        total_distance = sum(a.get("distance", 0) for a in year_activities)
        total_time = sum(a.get("moving_time", 0) for a in year_activities)
        
        # Criar markdown
        markdown = f"# Atividades do Strava - {year}\n\n"
        markdown += f"**Total de atividades:** {len(year_activities)}\n\n"
        
        markdown += "## Estatísticas do Ano\n\n"
        markdown += f"- **Distância total:** {format_distance(total_distance)}\n"
        markdown += f"- **Tempo total:** {format_duration(total_time)}\n"
        markdown += f"- **Média por atividade:** {format_distance(total_distance / len(year_activities))}\n\n"
        
        # Agrupar por tipo dentro do ano
        activities_by_type: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for activity in year_activities:
            sport_type = activity.get("sport_type", activity.get("type", "Outro"))
            activities_by_type[sport_type].append(activity)
        
        markdown += "## Resumo por Tipo de Atividade\n\n"
        markdown += "| Tipo | Quantidade | Distância Total | Tempo Total |\n"
        markdown += "|------|------------|-----------------|-------------|\n"
        
        for sport_type in sorted(activities_by_type.keys()):
            type_activities = activities_by_type[sport_type]
            type_distance = sum(a.get("distance", 0) for a in type_activities)
            type_time = sum(a.get("moving_time", 0) for a in type_activities)
            
            markdown += f"| {sport_type} | {len(type_activities)} | {format_distance(type_distance)} | {format_duration(type_time)} |\n"
        
        markdown += "\n"
        
        # Calcular recordes do ano e gerais
        year_records = calculate_records(year_activities)
        
        # Coletar todas as atividades até este ano (inclusive)
        all_activities_until_year = []
        for y in sorted(activities_by_year.keys()):
            if y <= year:
                all_activities_until_year.extend(activities_by_year[y])
        
        all_time_records = calculate_records(all_activities_until_year) if all_activities_until_year else {}
        
        # Usar formato de tabela comparativa
        markdown += format_records_comparison(year_records, all_time_records, year)
        
        markdown += "## Todas as Atividades\n\n"
        markdown += "| Data | Nome | Tipo | Distância | Duração | Pace | Elevação | Kudos |\n"
        markdown += "|------|------|------|-----------|---------|------|----------|-------|\n"
        
        for activity in year_activities:
            name = activity.get("name", "N/A")
            sport_type = activity.get("sport_type", activity.get("type", "N/A"))
            distance = activity.get("distance", 0)
            moving_time = activity.get("moving_time", 0)
            date = activity.get("start_date", "N/A")
            elevation = activity.get("total_elevation_gain", 0)
            kudos = activity.get("kudos_count", 0)
            
            date_formatted = format_date(date) if date != "N/A" else "N/A"
            distance_formatted = format_distance(distance)
            duration_formatted = format_duration(moving_time)
            pace_formatted = format_pace(distance, moving_time) if distance > 0 else "N/A"
            elevation_formatted = f"{elevation:.0f} m"
            
            markdown += f"| {date_formatted} | {name} | {sport_type} | {distance_formatted} | {duration_formatted} | {pace_formatted} | {elevation_formatted} | {kudos} |\n"
        
        # Salvar arquivo do ano
        output_file = output_path / f"strava_{year}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        created_files.append(str(output_file))
    
    # Criar arquivo índice
    create_index_file(activities_by_year, output_path)
    created_files.append(str(output_path / "README.md"))
    
    return created_files


def create_index_file(activities_by_year: Dict[int, List[Dict[str, Any]]], output_path: Path) -> None:
    """
    Cria arquivo índice com resumo de todos os anos.
    
    Args:
        activities_by_year: Atividades agrupadas por ano
        output_path: Caminho do diretório de saída
    """
    markdown = "# Atividades do Strava - Índice Geral\n\n"
    markdown += f"**Período:** {min(activities_by_year.keys())} - {max(activities_by_year.keys())}\n"
    
    total_all = sum(len(acts) for acts in activities_by_year.values())
    markdown += f"**Total de atividades:** {total_all}\n\n"
    
    markdown += "## Resumo por Ano\n\n"
    markdown += "| Ano | Atividades | Distância Total | Tempo Total | Arquivo |\n"
    markdown += "|-----|------------|-----------------|-------------|----------|\n"
    
    for year in sorted(activities_by_year.keys(), reverse=True):
        year_activities = activities_by_year[year]
        total_distance = sum(a.get("distance", 0) for a in year_activities)
        total_time = sum(a.get("moving_time", 0) for a in year_activities)
        
        markdown += f"| {year} | {len(year_activities)} | {format_distance(total_distance)} | {format_duration(total_time)} | [strava_{year}.md](strava_{year}.md) |\n"
    
    # Estatísticas gerais
    all_activities = [act for acts in activities_by_year.values() for act in acts]
    total_distance = sum(a.get("distance", 0) for a in all_activities)
    total_time = sum(a.get("moving_time", 0) for a in all_activities)
    
    markdown += "\n## Estatísticas Totais\n\n"
    markdown += f"- **Distância total:** {format_distance(total_distance)}\n"
    markdown += f"- **Tempo total:** {format_duration(total_time)}\n"
    markdown += f"- **Média por atividade:** {format_distance(total_distance / len(all_activities))}\n"
    markdown += f"- **Anos ativos:** {len(activities_by_year)}\n\n"
    
    # Adicionar recordes gerais
    all_time_records = calculate_records(all_activities)
    markdown += format_records_markdown(all_time_records, "Recordes Pessoais de Todos os Tempos")
    
    # Salvar índice
    with open(output_path / "README.md", "w", encoding="utf-8") as f:
        f.write(markdown)

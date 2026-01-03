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


def format_speed(meters_per_second: float) -> str:
    """Converte m/s para km/h formatado."""
    if meters_per_second == 0:
        return "N/A"
    km_per_hour = meters_per_second * 3.6
    return f"{km_per_hour:.1f} km/h"


def format_heartrate(bpm: float) -> str:
    """Formata frequência cardíaca."""
    if bpm == 0:
        return "N/A"
    return f"{int(bpm)} bpm"


def format_cadence(cadence: float, sport_type: str = "") -> str:
    """Formata cadência (RPM para bike, SPM para corrida)."""
    if cadence == 0:
        return "N/A"
    
    # Para corrida, a API retorna passos totais, precisamos dobrar
    if sport_type in ["Run", "Walk"]:
        unit = "spm"
        value = cadence * 2  # Converter para passos por minuto (ambas as pernas)
    else:
        unit = "rpm"
        value = cadence
    
    return f"{int(value)} {unit}"


def format_relative_effort(score: float) -> str:
    """Formata Relative Effort (Suffer Score)."""
    if not score or score == 0:
        return "N/A"
    return f"{int(score)}"


def calculate_relative_effort(
    moving_time: int,
    average_heartrate: float,
    max_heartrate: float = None,
    sport_type: str = "",
    user_max_hr: float = None
) -> int:
    """
    Calcula uma estimativa de Relative Effort (similar ao TRIMP).
    
    Baseado em:
    - Duração da atividade
    - Frequência cardíaca média
    - Tipo de atividade
    - FC máxima (se disponível)
    
    Args:
        moving_time: Tempo em movimento (segundos)
        average_heartrate: FC média (bpm)
        max_heartrate: FC máxima registrada na atividade (bpm)
        sport_type: Tipo de atividade
        user_max_hr: FC máxima do usuário (do perfil ou configuração)
        
    Returns:
        Escore estimado de esforço (0-1000+)
    """
    if not average_heartrate or average_heartrate == 0 or moving_time == 0:
        return 0
    
    # Usar FC máxima fornecida pelo usuário, se disponível
    if user_max_hr and user_max_hr > 0:
        estimated_max_hr = user_max_hr
    else:
        # Usar FC máxima da atividade como referência inicial
        if max_heartrate and max_heartrate > average_heartrate:
            estimated_max_hr = max_heartrate
        else:
            # Fallback: usar FC máxima padrão (220 - 35 anos)
            estimated_max_hr = 185
    
    # Calcular intensidade relativa (% da FC máxima)
    intensity = min(average_heartrate / estimated_max_hr, 1.0)  # Limitar a 100%
    
    # Fator de multiplicação por tipo de atividade
    activity_factors = {
        "Run": 1.2,      # Corrida é mais intensa
        "Ride": 1.0,     # Ciclismo base
        "Walk": 0.8,     # Caminhada menos intensa
        "Workout": 1.1,  # Treino funcional
        "Yoga": 0.6,     # Yoga menos intensa
    }
    
    factor = activity_factors.get(sport_type, 1.0)
    
    # Fórmula baseada em TRIMP exponencial
    # TRIMP = duration × intensity × exp(intensity)
    duration_minutes = moving_time / 60
    
    # Exponencial suavizado para não explodir o valor
    exp_factor = 1 + (intensity ** 1.5)
    
    # Calcular escore base
    effort = duration_minutes * intensity * exp_factor * factor
    
    # Escalar para ficar na faixa típica do Strava (0-300 comum, mas pode ir além)
    relative_effort = int(effort * 2.5)
    
    return relative_effort


def format_calories(calories: float) -> str:
    """Formata calorias."""
    if not calories or calories == 0:
        return "N/A"
    return f"{int(calories)} kcal"


def format_watts(watts: float) -> str:
    """Formata potência em watts."""
    if not watts or watts == 0:
        return "N/A"
    return f"{int(watts)} W"


def format_achievements(count: int) -> str:
    """Formata número de achievements."""
    if not count or count == 0:
        return "-"
    return f"{count}"


def format_prs(count: int) -> str:
    """Formata número de PRs (Personal Records)."""
    if not count or count == 0:
        return "-"
    return f"{count}"


def calculate_records(activities: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Calcula recordes pessoais por tipo de atividade.
    
    Args:
        activities: Lista de atividades
        
    Returns:
        Dicionário com recordes por tipo de atividade
    """
    records_by_type: Dict[str, Dict[str, Any]] = {}
    
    # Definir distâncias alvo por tipo de atividade (em metros)
    distance_targets = {
        "Ride": [1000, 5000, 10000, 20000],
        "Run": [1000, 5000, 10000],
        "Walk": [1000, 3000, 5000],
    }
    
    for activity in activities:
        sport_type = activity.get("sport_type", activity.get("type", "Outro"))
        distance = activity.get("distance", 0)
        moving_time = activity.get("moving_time", 0)
        elevation = activity.get("total_elevation_gain", 0)
        max_speed = activity.get("max_speed", 0)
        max_heartrate = activity.get("max_heartrate", 0)
        avg_watts = activity.get("average_watts", 0)
        max_watts = activity.get("max_watts", 0)
        
        if sport_type not in records_by_type:
            records_by_type[sport_type] = {
                "max_distance": {"value": 0, "activity": None},
                "max_time": {"value": 0, "activity": None},
                "max_elevation": {"value": 0, "activity": None},
                "best_pace": {"value": float('inf'), "activity": None},
                "max_speed": {"value": 0, "activity": None},
                "max_heartrate": {"value": 0, "activity": None},
                "max_avg_watts": {"value": 0, "activity": None},
                "max_watts": {"value": 0, "activity": None},
            }
            # Inicializar recordes de tempo por distância
            if sport_type in distance_targets:
                for target_dist in distance_targets[sport_type]:
                    key = f"best_time_{target_dist}m"
                    records_by_type[sport_type][key] = {"value": float('inf'), "activity": None}
        
        records = records_by_type[sport_type]
        
        # Definir pace máximo razoável por tipo de atividade (em segundos/km)
        max_pace_limits = {
            "Ride": 900,    # 15 min/km máximo para bike (muito lento em subidas íngremes)
            "Run": 1200,     # 20 min/km máximo para corrida (mais lento já seria caminhada)
            "Walk": 1200,   # 20 min/km máximo para caminhada
        }
        
        # Verificar se o pace da atividade é válido
        is_valid_pace = True
        if distance > 0 and moving_time > 0:
            current_pace = calculate_pace_seconds(distance, moving_time)
            max_pace = max_pace_limits.get(sport_type, 1800)
            if current_pace > max_pace:
                is_valid_pace = False
        
        # Maior distância (apenas se pace válido)
        if is_valid_pace and distance > records["max_distance"]["value"]:
            records["max_distance"]["value"] = distance
            records["max_distance"]["activity"] = activity
        
        # Maior tempo (apenas se pace válido)
        if is_valid_pace and moving_time > records["max_time"]["value"]:
            records["max_time"]["value"] = moving_time
            records["max_time"]["activity"] = activity
        
        # Maior elevação (apenas se pace válido)
        if is_valid_pace and elevation > records["max_elevation"]["value"]:
            records["max_elevation"]["value"] = elevation
            records["max_elevation"]["activity"] = activity
        
        # Melhor pace (apenas para atividades com distância e pace válido)
        if is_valid_pace and distance > 0:
            pace = calculate_pace_seconds(distance, moving_time)
            if pace < records["best_pace"]["value"]:
                records["best_pace"]["value"] = pace
                records["best_pace"]["activity"] = activity
        
        # Velocidade máxima
        if max_speed > records["max_speed"]["value"]:
            records["max_speed"]["value"] = max_speed
            records["max_speed"]["activity"] = activity
        
        # Frequência cardíaca máxima
        if max_heartrate > records["max_heartrate"]["value"]:
            records["max_heartrate"]["value"] = max_heartrate
            records["max_heartrate"]["activity"] = activity
        
        # Potência média máxima
        if avg_watts and avg_watts > records["max_avg_watts"]["value"]:
            records["max_avg_watts"]["value"] = avg_watts
            records["max_avg_watts"]["activity"] = activity
        
        # Potência máxima
        if max_watts and max_watts > records["max_watts"]["value"]:
            records["max_watts"]["value"] = max_watts
            records["max_watts"]["activity"] = activity
        
        # Melhor tempo para distâncias específicas
        if is_valid_pace and sport_type in distance_targets and distance > 0 and moving_time > 0:
            for target_dist in distance_targets[sport_type]:
                # Apenas considerar se a atividade tem pelo menos a distância alvo
                if distance >= target_dist:
                    key = f"best_time_{target_dist}m"
                    # Calcular o tempo estimado para essa distância (assumindo pace constante)
                    estimated_time = (target_dist / distance) * moving_time
                    
                    # Definir tempos mínimos razoáveis por distância (em segundos)
                    # para evitar registros incorretos
                    min_times = {
                        1000: 120,    # 1km: mínimo 2 minutos (pace 2:00/km - muito rápido mas possível)
                        3000: 420,    # 3km: mínimo 7 minutos (pace 2:20/km)
                        5000: 720,    # 5km: mínimo 12 minutos (pace 2:24/km)
                        10000: 1500,  # 10km: mínimo 25 minutos (pace 2:30/km)
                        20000: 3000,  # 20km: mínimo 50 minutos (pace 2:30/km)
                    }
                    
                    # Apenas atualizar se o tempo é razoável
                    if estimated_time >= min_times.get(target_dist, 0) and estimated_time < records[key]["value"]:
                        records[key]["value"] = estimated_time
                        records[key]["activity"] = activity
    
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
        
        # Velocidade máxima
        if records["max_speed"]["activity"]:
            act = records["max_speed"]["activity"]
            speed = format_speed(act.get('max_speed', 0))
            markdown += f"- **Velocidade Máxima:** {speed}"
            markdown += f" - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})\n"
        
        # Frequência cardíaca máxima
        if records["max_heartrate"]["activity"]:
            act = records["max_heartrate"]["activity"]
            hr = format_heartrate(act.get('max_heartrate', 0))
            markdown += f"- **FC Máxima:** {hr}"
            markdown += f" - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})\n"
        
        # Potência média máxima (apenas para atividades com medidor de potência)
        if records["max_avg_watts"]["activity"]:
            act = records["max_avg_watts"]["activity"]
            watts = format_watts(act.get('average_watts', 0))
            markdown += f"- **Maior Potência Média:** {watts}"
            markdown += f" - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})\n"
        
        # Potência máxima
        if records["max_watts"]["activity"]:
            act = records["max_watts"]["activity"]
            watts = format_watts(act.get('max_watts', 0))
            markdown += f"- **Potência Máxima:** {watts}"
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
        
        # Maior distância (não mostrar para Workout e Yoga)
        if sport_type not in ["Workout", "Yoga"]:
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
        
        # Adicionar tempos para distâncias específicas
        distance_targets = {
            "Ride": [1000, 5000, 10000, 20000],
            "Run": [1000, 5000, 10000],
            "Walk": [1000, 3000, 5000],
        }
        
        if sport_type in distance_targets:
            for target_dist in distance_targets[sport_type]:
                key = f"best_time_{target_dist}m"
                dist_km = target_dist / 1000
                
                year_best_time = ""
                if year_rec.get(key, {}).get("activity") and year_rec.get(key, {}).get("value") != float('inf'):
                    time_val = year_rec[key]["value"]
                    act = year_rec[key]["activity"]
                    year_best_time = f"{format_duration(int(time_val))} - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})"
                
                all_best_time = ""
                if all_rec.get(key, {}).get("activity") and all_rec.get(key, {}).get("value") != float('inf'):
                    time_val = all_rec[key]["value"]
                    act = all_rec[key]["activity"]
                    all_best_time = f"{format_duration(int(time_val))} - *{act.get('name', 'N/A')}* ({format_date(act.get('start_date', ''))})"
                
                if year_best_time or all_best_time:
                    label = f"**Melhor Tempo {dist_km:.0f}km**" if dist_km >= 1 else f"**Melhor Tempo {dist_km}km**"
                    markdown += f"| {label} | {year_best_time or 'N/A'} | {all_best_time or 'N/A'} |\n"
        
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


def activities_to_markdown_by_year(activities: List[Dict[str, Any]], output_dir: str = "atividades", user_max_hr: float = None) -> tuple[List[str], float, str]:
    """
    Converte lista de atividades para formato Markdown separado por ano.
    
    Args:
        activities: Lista de atividades do Strava
        output_dir: Diretório para salvar os arquivos
        user_max_hr: FC máxima do usuário (opcional)
        
    Returns:
        Tupla com (lista de arquivos criados, FC detectada, data da detecção)
    """
    # Criar diretório se não existir
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Variáveis para retorno
    detected_max_hr = None
    detection_date = None
    
    # Se não fornecida, detectar FC máxima dos dados históricos RECENTES
    if not user_max_hr:
        # Priorizar atividades dos últimos 6 meses para FC máxima
        from datetime import timedelta, timezone
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
        recent_activities = [
            a for a in activities 
            if a.get("start_date") and datetime.fromisoformat(a["start_date"].replace("Z", "+00:00")) >= six_months_ago
        ]
        
        # Buscar FC máxima nas atividades recentes
        recent_max_hrs = [
            (a.get("max_heartrate", 0), a.get("start_date", ""), a.get("name", ""))
            for a in recent_activities 
            if a.get("max_heartrate", 0) > 0
        ]
        
        if recent_max_hrs:
            # Ordenar por FC máxima
            recent_max_hrs.sort(key=lambda x: x[0], reverse=True)
            
            # Pegar as 10 maiores FCs
            top_hrs = [hr for hr, _, _ in recent_max_hrs[:10]]
            max_detected = max(top_hrs)
            
            # Detectar outliers (FCs irrealistas acima de 200 bpm)
            # Usar percentil 95 em vez do máximo absoluto
            if max_detected > 200:
                # Filtrar valores extremos e usar percentil 95
                realistic_hrs = [hr for hr in top_hrs if hr <= 200]
                if not realistic_hrs:
                    # Se todas são altas, usar percentil 95 de todas
                    realistic_hrs = sorted([hr for hr, _, _ in recent_max_hrs])
                    percentile_95_idx = int(len(realistic_hrs) * 0.95)
                    detected_max_hr = realistic_hrs[percentile_95_idx]
                    # Encontrar a data desse valor
                    for hr, date, name in recent_max_hrs:
                        if hr == detected_max_hr:
                            detection_date = date
                            break
                    user_max_hr = detected_max_hr
                    print(f"\n💓 FC Máxima detectada: {int(detected_max_hr)} bpm (percentil 95)")
                    print(f"   ⚠️  Ignorados valores suspeitos acima de 200 bpm (possíveis erros de sensor)")
                    print(f"   💡 Valor mais alto detectado: {int(max_detected)} bpm - provavelmente erro")
                else:
                    # Encontrar a data do valor máximo realista
                    for hr, date, name in recent_max_hrs:
                        if hr == max(realistic_hrs):
                            detected_max_hr = hr
                            detection_date = date
                            break
                    user_max_hr = detected_max_hr
                    year = detection_date[:4] if detection_date else "?"
                    print(f"\n💓 FC Máxima detectada: {int(detected_max_hr)} bpm (última vez em {year})")
                    print(f"   ⚠️  Ignorado valor de {int(max_detected)} bpm (provável erro de sensor)")
            else:
                detected_max_hr, detection_date, name = recent_max_hrs[0]
                user_max_hr = detected_max_hr
                year = detection_date[:4] if detection_date else "?"
                print(f"\n💓 FC Máxima detectada: {int(detected_max_hr)} bpm (última vez em {year})")
                print(f"   Atividade: {name}")
            
            print(f"   Baseado nas atividades dos últimos 6 meses")
        else:
            # Fallback: buscar em todo histórico se não houver dados recentes
            all_max_hrs = [
                (a.get("max_heartrate", 0), a.get("start_date", ""))
                for a in activities 
                if a.get("max_heartrate", 0) > 0
            ]
            if all_max_hrs:
                all_max_hrs.sort(key=lambda x: x[0], reverse=True)
                max_detected = all_max_hrs[0][0]
                
                # Detectar outliers mesmo no histórico
                if max_detected > 200:
                    realistic_hrs = sorted([hr for hr, _ in all_max_hrs if hr <= 200])
                    if realistic_hrs:
                        detected_max_hr = max(realistic_hrs)
                        # Encontrar a data
                        for hr, date in all_max_hrs:
                            if hr == detected_max_hr:
                                detection_date = date
                                break
                    else:
                        # Usar percentil 95
                        all_hrs = sorted([hr for hr, _ in all_max_hrs])
                        percentile_95_idx = int(len(all_hrs) * 0.95)
                        detected_max_hr = all_hrs[percentile_95_idx]
                        # Encontrar a data do percentil
                        for hr, date in all_max_hrs:
                            if hr == detected_max_hr:
                                detection_date = date
                                break
                    
                    user_max_hr = detected_max_hr
                    print(f"\n💓 FC Máxima detectada: {int(detected_max_hr)} bpm")
                    print(f"   ⚠️  Ignorado valor de {int(max_detected)} bpm (provável erro de sensor)")
                    print(f"   ⚠️  Dados antigos - considere configurar USER_MAX_HR no .env")
                else:
                    detected_max_hr, detection_date = all_max_hrs[0]
                    user_max_hr = detected_max_hr
                    year = detection_date[:4] if detection_date else "?"
                    print(f"\n💓 FC Máxima detectada: {int(detected_max_hr)} bpm (registrada em {year})")
                    print(f"   ⚠️  Dado antigo - considere configurar USER_MAX_HR no .env se souber sua FC atual")
            else:
                # Usar FC máxima baseada em idade (220 - 40 = 180)
                user_max_hr = 180
                print(f"\n💓 Sem dados de FC disponíveis. Usando FC baseada em idade: 180 bpm (220 - 40 anos)")
                print(f"   💡 Configure USER_MAX_HR no .env para cálculos mais precisos")
    
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
        markdown += f"**Total de atividades:** {len(year_activities)}\n"
        if user_max_hr:
            markdown += f"**FC Máxima utilizada nos cálculos:** {int(user_max_hr)} bpm\n"
        markdown += "\n"
        
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
        markdown += "| Tipo | Quantidade | Distância Total | Tempo Total | Vel. Média | FC Média | Cadência Média |\n"
        markdown += "|------|------------|-----------------|-------------|------------|----------|----------------|\n"
        
        for sport_type in sorted(activities_by_type.keys()):
            type_activities = activities_by_type[sport_type]
            type_distance = sum(a.get("distance", 0) for a in type_activities)
            type_time = sum(a.get("moving_time", 0) for a in type_activities)
            
            # Calcular médias (apenas atividades com dados)
            speeds = [a.get("average_speed", 0) for a in type_activities if a.get("average_speed", 0) > 0]
            avg_speed = sum(speeds) / len(speeds) if speeds else 0
            
            hrs = [a.get("average_heartrate", 0) for a in type_activities if a.get("average_heartrate", 0) > 0]
            avg_hr = sum(hrs) / len(hrs) if hrs else 0
            
            cadences = [a.get("average_cadence", 0) for a in type_activities if a.get("average_cadence", 0) > 0]
            avg_cadence = sum(cadences) / len(cadences) if cadences else 0
            
            markdown += f"| {sport_type} | {len(type_activities)} | {format_distance(type_distance)} | {format_duration(type_time)} | {format_speed(avg_speed)} | {format_heartrate(avg_hr)} | {format_cadence(avg_cadence, sport_type)} |\n"
        
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
        markdown += "| Data | Nome | Tipo | Distância | Duração | Vel. Média | FC Média | Cadência | Relative Effort | Calorias | Potência | PRs |\n"
        markdown += "|------|------|------|-----------|---------|------------|----------|----------|-----------------|----------|----------|-----|\n"
        
        for activity in year_activities:
            name = activity.get("name", "N/A")
            sport_type = activity.get("sport_type", activity.get("type", "N/A"))
            distance = activity.get("distance", 0)
            moving_time = activity.get("moving_time", 0)
            date = activity.get("start_date", "N/A")
            avg_speed = activity.get("average_speed", 0)
            avg_hr = activity.get("average_heartrate", 0)
            max_hr = activity.get("max_heartrate", 0)
            avg_cadence = activity.get("average_cadence", 0)
            suffer_score = activity.get("suffer_score")
            calories = activity.get("calories")
            avg_watts = activity.get("average_watts")
            pr_count = activity.get("pr_count", 0)
            
            # Calcular Relative Effort localmente se não disponível
            if not suffer_score and avg_hr:
                suffer_score = calculate_relative_effort(
                    moving_time, avg_hr, max_hr, sport_type, user_max_hr
                )
            
            date_formatted = format_date(date) if date != "N/A" else "N/A"
            distance_formatted = format_distance(distance)
            duration_formatted = format_duration(moving_time)
            speed_formatted = format_speed(avg_speed)
            hr_formatted = format_heartrate(avg_hr)
            cadence_formatted = format_cadence(avg_cadence, sport_type)
            effort_formatted = format_relative_effort(suffer_score)
            calories_formatted = format_calories(calories)
            watts_formatted = format_watts(avg_watts)
            pr_formatted = format_prs(pr_count)
            
            markdown += f"| {date_formatted} | {name} | {sport_type} | {distance_formatted} | {duration_formatted} | {speed_formatted} | {hr_formatted} | {cadence_formatted} | {effort_formatted} | {calories_formatted} | {watts_formatted} | {pr_formatted} |\n"
        
        # Salvar arquivo do ano
        output_file = output_path / f"strava_{year}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        created_files.append(str(output_file))
    
    # Criar arquivo de estatísticas anuais
    create_annual_statistics_file(activities_by_year, output_path)
    created_files.append(str(output_path / "estatisticas_anuais.md"))
    
    # Criar arquivo índice
    create_index_file(activities_by_year, output_path)
    created_files.append(str(output_path / "README.md"))
    
    return created_files, detected_max_hr, detection_date


def create_annual_statistics_file(activities_by_year: Dict[int, List[Dict[str, Any]]], output_path: Path) -> None:
    """
    Cria arquivo com estatísticas anuais e gráficos.
    
    Args:
        activities_by_year: Atividades agrupadas por ano
        output_path: Caminho do diretório de saída
    """
    markdown = "# Estatísticas Anuais do Strava\n\n"
    markdown += "Visão geral das atividades ao longo dos anos.\n\n"
    
    # Tabela resumo
    markdown += "## Resumo Geral\n\n"
    markdown += "| Ano | Total de Atividades | Distância Total | Tempo Total |\n"
    markdown += "|-----|---------------------|-----------------|-------------|\n"
    
    years_data = []
    for year in sorted(activities_by_year.keys()):
        year_activities = activities_by_year[year]
        total_distance = sum(a.get("distance", 0) for a in year_activities)
        total_time = sum(a.get("moving_time", 0) for a in year_activities)
        
        years_data.append({
            "year": year,
            "count": len(year_activities),
            "distance": total_distance / 1000,  # km
            "time": total_time / 3600  # horas
        })
        
        markdown += f"| {year} | {len(year_activities)} | {format_distance(total_distance)} | {format_duration(total_time)} |\n"
    
    # Gráfico de distância
    markdown += "\n## Gráfico de Distância Total por Ano\n\n"
    markdown += "```mermaid\n"
    markdown += "xychart-beta\n"
    markdown += '    title "Distância Total por Ano (km)"\n'
    markdown += f"    x-axis [{', '.join(str(d['year']) for d in years_data)}]\n"
    max_distance = max(d['distance'] for d in years_data)
    markdown += f"    y-axis \"Distância (km)\" 0 --> {int(max_distance * 1.1)}\n"
    markdown += f"    bar [{', '.join(str(int(d['distance'])) for d in years_data)}]\n"
    markdown += "```\n\n"
    
    # Gráfico de tempo
    markdown += "## Gráfico de Tempo Total por Ano\n\n"
    markdown += "```mermaid\n"
    markdown += "xychart-beta\n"
    markdown += '    title "Tempo Total por Ano (horas)"\n'
    markdown += f"    x-axis [{', '.join(str(d['year']) for d in years_data)}]\n"
    max_time = max(d['time'] for d in years_data)
    markdown += f"    y-axis \"Tempo (horas)\" 0 --> {int(max_time * 1.1)}\n"
    markdown += f"    bar [{', '.join(str(int(d['time'])) for d in years_data)}]\n"
    markdown += "```\n\n"
    
    # Gráfico de atividades
    markdown += "## Gráfico de Número de Atividades por Ano\n\n"
    markdown += "```mermaid\n"
    markdown += "xychart-beta\n"
    markdown += '    title "Número de Atividades por Ano"\n'
    markdown += f"    x-axis [{', '.join(str(d['year']) for d in years_data)}]\n"
    max_count = max(d['count'] for d in years_data)
    markdown += f"    y-axis \"Atividades\" 0 --> {int(max_count * 1.1)}\n"
    markdown += f"    bar [{', '.join(str(d['count']) for d in years_data)}]\n"
    markdown += "```\n\n"
    
    # Gráfico de evolução combinado
    markdown += "## Evolução Anual\n\n"
    markdown += "```mermaid\n"
    markdown += "xychart-beta\n"
    markdown += '    title "Evolução: Distância vs Tempo"\n'
    markdown += f"    x-axis [{', '.join(str(d['year']) for d in years_data)}]\n"
    max_value = max(max_distance, max_time * 10)
    markdown += f"    y-axis \"Escala normalizada\" 0 --> {int(max_value * 1.1)}\n"
    markdown += f"    line \"Distância (km)\" [{', '.join(str(int(d['distance'])) for d in years_data)}]\n"
    markdown += f"    line \"Tempo (horas)\" [{', '.join(str(int(d['time'])) for d in years_data)}]\n"
    markdown += "```\n\n"
    
    # Insights
    markdown += "## Insights\n\n"
    max_activities_year = max(years_data, key=lambda x: x['count'])
    max_distance_year = max(years_data, key=lambda x: x['distance'])
    max_time_year = max(years_data, key=lambda x: x['time'])
    
    markdown += f"- **Pico de atividades:** {max_activities_year['year']} com {max_activities_year['count']} atividades registradas\n"
    markdown += f"- **Maior distância:** {max_distance_year['year']} com {max_distance_year['distance']:.2f} km percorridos\n"
    markdown += f"- **Maior tempo:** {max_time_year['year']} com {int(max_time_year['time'])}:{int((max_time_year['time'] % 1) * 60):02d}:00 horas de atividade\n"
    
    if len(years_data) >= 3:
        recent_years = years_data[-3:]
        avg_activities = sum(d['count'] for d in recent_years) / len(recent_years)
        markdown += f"- **Média recente ({recent_years[0]['year']}-{recent_years[-1]['year']}):** {avg_activities:.0f} atividades por ano\n"
    
    # Salvar arquivo
    with open(output_path / "estatisticas_anuais.md", "w", encoding="utf-8") as f:
        f.write(markdown)


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
    
    # Link para estatísticas anuais
    markdown += "## Visualizações\n\n"
    markdown += "- 📊 [Estatísticas Anuais com Gráficos](estatisticas_anuais.md)\n\n"
    
    # Adicionar recordes gerais
    all_time_records = calculate_records(all_activities)
    markdown += format_records_markdown(all_time_records, "Recordes Pessoais de Todos os Tempos")
    
    # Salvar índice
    with open(output_path / "README.md", "w", encoding="utf-8") as f:
        f.write(markdown)

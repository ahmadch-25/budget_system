def is_hour_in_range(start: int, end: int, hour: int) -> bool:
    if start < end:
        return start <= hour < end
    else:  # wraparound, like 22–2
        return hour >= start or hour < end

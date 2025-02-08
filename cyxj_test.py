def standardize_date_day(date_str):
    """
    Standardize different date formats to time_cyxj common format 'YYYY-MM-DD HH:MM'.

    Args:
    date_str (str): The date string in varied formats.

    Returns:
    str: The standardized date string.
    """
    # Define the formats to be standardized
    format_1 = '%Y年%m月%d日'
    format_2 = '%Y.%m.%d'
    format_3 = '%Y-%m-%d'
    date_str = str(date_str)
    # Try to parse and standardize the date string
    try:
        if '年' in date_str:
            return datetime.strptime(date_str, format_1).strftime('%Y-%m-%d')
        elif '.' in date_str:
            return datetime.strptime(date_str, format_2).strftime('%Y-%m-%d')
        elif '-' in date_str:
            return datetime.strptime(date_str, format_3).strftime('%Y-%m-%d')
        else:
            return f"Error format of {date_str}"
    except ValueError as e:
        return f"Error: {str(e)}"
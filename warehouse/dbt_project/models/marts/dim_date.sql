with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2023-01-01' as date)",
        end_date="cast('2027-01-01' as date)"
    ) }}
)
select
    cast(extract(year from date_day) * 10000 + extract(month from date_day) * 100 + extract(day from date_day) as integer) as date_key,
    cast(date_day as date)                         as date_day,
    extract(year    from date_day)                 as year,
    extract(quarter from date_day)                 as quarter,
    extract(month   from date_day)                 as month,
    extract(day     from date_day)                 as day_of_month,
    {% if target.name == 'postgres' %}
    extract(dow from date_day)                     as day_of_week,
    trim(to_char(date_day, 'Day'))                 as day_name
    {% elif target.name == 'bigquery' %}
    extract(dayofweek from date_day) - 1           as day_of_week,
    format_date('%A', date_day)                    as day_name
    {% else %}
    dayofweek(date_day)                            as day_of_week,
    dayname(date_day)                              as day_name
    {% endif %}
from spine

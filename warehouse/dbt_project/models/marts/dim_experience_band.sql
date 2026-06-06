-- Experience-band dimension with display order.
select 'Entry (0-2)' as experience_band, 1 as band_order union all
select 'Mid (3-5)' as experience_band, 2 as band_order union all
select 'Senior (6-10)' as experience_band, 3 as band_order union all
select 'Lead (10+)' as experience_band, 4 as band_order union all
select 'Not specified' as experience_band, 5 as band_order

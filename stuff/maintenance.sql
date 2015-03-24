-- check for orphan annotations
select count(*) from series_tag where created_by is null;

-- fill created, modified in series_tag from sample_tag
update series_tag S set created_by = T.created_by, created_on = T.created_on, modified_by = T.modified_by, modified_on = T.modified_on FROM sample_tag T where T.series_tag_id = S.id and S.created_by is null;


-- check if all validation jobs are scheduled
select count(*) from series_tag T where
    T.id not in (select series_tag_id from series_validation)
    and T.id not in (select series_tag_id from validation_job)
    and T.created_by is not null;

--- schedule validation jobs
insert into validation_job (series_tag_id) select T.id from series_tag T where
    T.id not in (select series_tag_id from series_validation)
    and T.id not in (select series_tag_id from validation_job)
    and T.created_by is not null;


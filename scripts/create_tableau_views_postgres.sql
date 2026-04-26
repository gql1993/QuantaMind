CREATE OR REPLACE VIEW public.vw_pgvector_chunks AS
SELECT
    id AS chunk_id,
    source,
    title,
    left(content, 300) AS content_preview,
    jsonb_array_length(COALESCE(keywords, '[]'::jsonb)) AS keyword_count,
    updated_at
FROM public.knowledge_chunks;


CREATE OR REPLACE VIEW public.vw_pgvector_source_summary AS
SELECT
    source,
    count(*) AS chunk_count,
    min(updated_at) AS first_updated_at,
    max(updated_at) AS last_updated_at
FROM public.knowledge_chunks
GROUP BY source
ORDER BY chunk_count DESC, source;


CREATE OR REPLACE VIEW public.vw_pgvector_daily_activity AS
SELECT
    date_trunc('day', updated_at) AS day,
    count(*) AS chunk_count,
    count(DISTINCT source) AS source_count
FROM public.knowledge_chunks
GROUP BY 1
ORDER BY 1 DESC;


CREATE OR REPLACE VIEW public.vw_quantamind_pulse_calibration_history AS
SELECT
    id,
    calibration_key,
    payload ->> 'source' AS source,
    payload ->> 'qubit' AS qubit,
    payload ->> 'gate' AS gate,
    NULLIF(payload ->> 'value_ghz', '')::double precision AS value_ghz,
    NULLIF(payload ->> 'value', '')::double precision AS value,
    NULLIF(payload ->> 'fidelity_pct', '')::double precision AS fidelity_pct,
    NULLIF(payload ->> 'readout_freq_ghz', '')::double precision AS readout_freq_ghz,
    NULLIF(payload ->> 'readout_angle_deg', '')::double precision AS readout_angle_deg,
    NULLIF(payload ->> 'assignment_fidelity_pct', '')::double precision AS assignment_fidelity_pct,
    NULLIF(payload ->> 'T1_us', '')::double precision AS t1_us,
    NULLIF(payload ->> 'fit_error_us', '')::double precision AS fit_error_us,
    payload ->> 'quality' AS quality,
    recorded_at
FROM public.quantamind_pulse_calibration_history
ORDER BY recorded_at DESC;


CREATE OR REPLACE VIEW public.vw_quantamind_pipeline_history AS
SELECT
    pipeline_id,
    payload ->> 'name' AS name,
    payload ->> 'template' AS template,
    payload ->> 'status' AS status,
    NULLIF(payload ->> 'current_stage', '')::int AS current_stage,
    payload ->> 'current_step' AS current_step,
    COALESCE(jsonb_array_length(payload -> 'steps'), 0) AS steps_count,
    payload ->> 'created_at' AS created_at,
    payload ->> 'started_at' AS started_at,
    payload ->> 'completed_at' AS completed_at,
    updated_at
FROM public.quantamind_pipelines
ORDER BY updated_at DESC;


CREATE OR REPLACE VIEW public.vw_quantamind_pipeline_steps AS
SELECT
    p.pipeline_id,
    p.payload ->> 'name' AS pipeline_name,
    step.value ->> 'agent' AS agent,
    step.value ->> 'title' AS title,
    step.value ->> 'tool' AS tool,
    step.value ->> 'status' AS status,
    NULLIF(step.value ->> 'stage', '')::int AS stage,
    step.value ->> 'started_at' AS started_at,
    step.value ->> 'completed_at' AS completed_at
FROM public.quantamind_pipelines p
CROSS JOIN LATERAL jsonb_array_elements(COALESCE(p.payload -> 'steps', '[]'::jsonb)) AS step(value);

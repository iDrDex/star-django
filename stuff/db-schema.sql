--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: star; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE star WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';


ALTER DATABASE star OWNER TO postgres;

\connect star

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: array_uniq(anyarray); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION array_uniq(anyarray) RETURNS anyarray
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$
    select array(select distinct unnest($1))
$_$;


ALTER FUNCTION public.array_uniq(anyarray) OWNER TO postgres;

--
-- Name: concat_tsvectors(tsvector, tsvector); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION concat_tsvectors(tsv1 tsvector, tsv2 tsvector) RETURNS tsvector
    LANGUAGE plpgsql
    AS $$
        BEGIN
          RETURN coalesce(tsv1, to_tsvector('english', ''))
                 || coalesce(tsv2, to_tsvector('english', ''));
        END;
        $$;


ALTER FUNCTION public.concat_tsvectors(tsv1 tsvector, tsv2 tsvector) OWNER TO postgres;

--
-- Name: make_attrs_tsv(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION make_attrs_tsv() RETURNS trigger
    LANGUAGE plpgsql STABLE
    AS $$
declare
  tmp text;
begin
  NEW.tsv = to_tsvector('english', (select string_agg(value, ' ') from json_each_text(NEW.attrs::JSON)));
  return NEW;
end;
$$;


ALTER FUNCTION public.make_attrs_tsv() OWNER TO postgres;

--
-- Name: array_concat(anyarray); Type: AGGREGATE; Schema: public; Owner: postgres
--

CREATE AGGREGATE array_concat(anyarray) (
    SFUNC = array_cat,
    STYPE = anyarray,
    INITCOND = '{}'
);


ALTER AGGREGATE public.array_concat(anyarray) OWNER TO postgres;

--
-- Name: array_concat_uniq(anyarray); Type: AGGREGATE; Schema: public; Owner: postgres
--

CREATE AGGREGATE array_concat_uniq(anyarray) (
    SFUNC = array_cat,
    STYPE = anyarray,
    INITCOND = '{}',
    FINALFUNC = array_uniq
);


ALTER AGGREGATE public.array_concat_uniq(anyarray) OWNER TO postgres;

--
-- Name: tsvector_agg(tsvector); Type: AGGREGATE; Schema: public; Owner: postgres
--

CREATE AGGREGATE tsvector_agg(tsvector) (
    SFUNC = concat_tsvectors,
    STYPE = tsvector,
    INITCOND = ''
);


ALTER AGGREGATE public.tsvector_agg(tsvector) OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: analysis; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE analysis (
    id integer NOT NULL,
    analysis_name character varying(512),
    description character varying(512),
    case_query character varying(512),
    control_query character varying(512),
    modifier_query character varying(512),
    series_count integer,
    platform_count integer,
    sample_count integer,
    series_ids text,
    platform_ids text,
    sample_ids text,
    is_active boolean NOT NULL,
    created_on timestamp without time zone,
    created_by integer,
    modified_on timestamp without time zone,
    modified_by integer,
    min_samples integer,
    df text,
    fold_changes text,
    success boolean NOT NULL,
    specie character varying(127) NOT NULL
);


ALTER TABLE public.analysis OWNER TO postgres;

--
-- Name: analysis_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE analysis_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.analysis_id_seq OWNER TO postgres;

--
-- Name: analysis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE analysis_id_seq OWNED BY analysis.id;


--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_group (
    id integer NOT NULL,
    name character varying(80) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO postgres;

--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_group_permissions (
    id integer NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO postgres;

--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    codename character varying(100) NOT NULL,
    content_type_id integer NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO postgres;

--
-- Name: auth_user; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(127) NOT NULL,
    first_name character varying(30) NOT NULL,
    last_name character varying(30) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    is_competent boolean NOT NULL
);


ALTER TABLE public.auth_user OWNER TO postgres;

--
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_user_groups (
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.auth_user_groups OWNER TO postgres;

--
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE auth_user_user_permissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_user_user_permissions OWNER TO postgres;

--
-- Name: authtoken_token; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE authtoken_token (
    key character varying(40) NOT NULL,
    created timestamp with time zone NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.authtoken_token OWNER TO postgres;

--
-- Name: balanced_meta; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE balanced_meta (
    id integer NOT NULL,
    analysis_id integer,
    mygene_sym character varying(512),
    mygene_entrez integer,
    direction character varying(512),
    k double precision,
    te_fixed double precision,
    te_random double precision,
    pval_fixed double precision,
    pval_random double precision,
    c double precision,
    h double precision,
    i2 double precision,
    q double precision,
    te double precision,
    te_tau double precision,
    casedatacount double precision,
    comb_fixed double precision,
    comb_random double precision,
    controldatacount double precision,
    data double precision,
    df_q double precision,
    lower_fixed double precision,
    lower_predict double precision,
    lower_random double precision,
    mean_c double precision,
    mean_e double precision,
    n_c double precision,
    n_e double precision,
    sd_c double precision,
    sd_e double precision,
    se_tau2 double precision,
    sete double precision,
    sete_fixed double precision,
    sete_random double precision,
    tau double precision,
    tau_common double precision,
    upper_fixed double precision,
    upper_random double precision,
    version character varying(512),
    zval_fixed double precision,
    zval_random double precision
);


ALTER TABLE public.balanced_meta OWNER TO postgres;

--
-- Name: balanced_meta_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE balanced_meta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.balanced_meta_id_seq OWNER TO postgres;

--
-- Name: balanced_meta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE balanced_meta_id_seq OWNED BY balanced_meta.id;


--
-- Name: core_statisticcache; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE core_statisticcache (
    id integer NOT NULL,
    slug character varying(30) NOT NULL,
    count integer NOT NULL,
    CONSTRAINT core_statisticcache_count_check CHECK ((count >= 0))
);


ALTER TABLE public.core_statisticcache OWNER TO postgres;

--
-- Name: core_statisticcache_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE core_statisticcache_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.core_statisticcache_id_seq OWNER TO postgres;

--
-- Name: core_statisticcache_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE core_statisticcache_id_seq OWNED BY core_statisticcache.id;


--
-- Name: count; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE count (
    id integer NOT NULL,
    what character varying(512),
    count integer
);


ALTER TABLE public.count OWNER TO postgres;

--
-- Name: count_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE count_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.count_id_seq OWNER TO postgres;

--
-- Name: count_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE count_id_seq OWNED BY count.id;


--
-- Name: dauth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE dauth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dauth_group_id_seq OWNER TO postgres;

--
-- Name: dauth_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE dauth_group_id_seq OWNED BY auth_group.id;


--
-- Name: dauth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE dauth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dauth_group_permissions_id_seq OWNER TO postgres;

--
-- Name: dauth_group_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE dauth_group_permissions_id_seq OWNED BY auth_group_permissions.id;


--
-- Name: dauth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE dauth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dauth_permission_id_seq OWNER TO postgres;

--
-- Name: dauth_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE dauth_permission_id_seq OWNED BY auth_permission.id;


--
-- Name: dauth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE dauth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dauth_user_groups_id_seq OWNER TO postgres;

--
-- Name: dauth_user_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE dauth_user_groups_id_seq OWNED BY auth_user_groups.id;


--
-- Name: dauth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE dauth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dauth_user_id_seq OWNER TO postgres;

--
-- Name: dauth_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE dauth_user_id_seq OWNED BY auth_user.id;


--
-- Name: dauth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE dauth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dauth_user_user_permissions_id_seq OWNER TO postgres;

--
-- Name: dauth_user_user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE dauth_user_user_permissions_id_seq OWNED BY auth_user_user_permissions.id;


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_admin_log_id_seq OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_admin_log_id_seq OWNED BY django_admin_log.id;


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_content_type_id_seq OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_content_type_id_seq OWNED BY django_content_type.id;


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_migrations (
    id integer NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.django_migrations_id_seq OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE django_migrations_id_seq OWNED BY django_migrations.id;


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO postgres;

--
-- Name: meta_analysis; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE meta_analysis (
    id integer NOT NULL,
    analysis_id integer NOT NULL,
    mygene_sym character varying(512),
    mygene_entrez integer NOT NULL,
    direction character varying(512),
    casedatacount integer NOT NULL,
    controldatacount integer NOT NULL,
    k integer NOT NULL,
    fixed_te double precision,
    fixed_se double precision,
    fixed_lower double precision,
    fixed_upper double precision,
    fixed_pval double precision,
    fixed_zscore double precision,
    random_te double precision,
    random_se double precision,
    random_lower double precision,
    random_upper double precision,
    random_pval double precision,
    random_zscore double precision,
    predict_te double precision,
    predict_se double precision,
    predict_lower double precision,
    predict_upper double precision,
    predict_pval double precision,
    predict_zscore double precision,
    tau2 double precision,
    tau2_se double precision,
    c double precision,
    h double precision,
    h_lower double precision,
    h_upper double precision,
    i2 double precision,
    i2_lower double precision,
    i2_upper double precision,
    q double precision,
    q_df double precision
);


ALTER TABLE public.meta_analysis OWNER TO postgres;

--
-- Name: meta_analysis_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE meta_analysis_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.meta_analysis_id_seq OWNER TO postgres;

--
-- Name: meta_analysis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE meta_analysis_id_seq OWNED BY meta_analysis.id;


--
-- Name: platform; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE platform (
    id integer NOT NULL,
    gpl_name text,
    specie character varying(127) NOT NULL,
    last_filled timestamp with time zone,
    stats text NOT NULL,
    verdict character varying(127) NOT NULL,
    history text NOT NULL,
    probes_matched integer,
    probes_total integer
);


ALTER TABLE public.platform OWNER TO postgres;

--
-- Name: platform_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE platform_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.platform_id_seq OWNER TO postgres;

--
-- Name: platform_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE platform_id_seq OWNED BY platform.id;


--
-- Name: platform_probe; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE platform_probe (
    id integer NOT NULL,
    platform_id integer NOT NULL,
    probe text,
    mygene_sym text,
    mygene_entrez integer NOT NULL
);


ALTER TABLE public.platform_probe OWNER TO postgres;

--
-- Name: platform_probe_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE platform_probe_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.platform_probe_id_seq OWNER TO postgres;

--
-- Name: platform_probe_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE platform_probe_id_seq OWNED BY platform_probe.id;


--
-- Name: platform_stats; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE platform_stats (
    platform_id integer,
    probes_matched_old integer
);


ALTER TABLE public.platform_stats OWNER TO postgres;

--
-- Name: sample; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE sample (
    id integer NOT NULL,
    series_id integer NOT NULL,
    platform_id integer NOT NULL,
    gsm_name text,
    deleted character(1),
    attrs text NOT NULL
);


ALTER TABLE public.sample OWNER TO postgres;

--
-- Name: sample_annotation; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE sample_annotation (
    id integer NOT NULL,
    annotation text NOT NULL,
    sample_id integer NOT NULL,
    serie_annotation_id integer NOT NULL
);


ALTER TABLE public.sample_annotation OWNER TO postgres;

--
-- Name: sample_annotation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sample_annotation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_annotation_id_seq OWNER TO postgres;

--
-- Name: sample_annotation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE sample_annotation_id_seq OWNED BY sample_annotation.id;


--
-- Name: sample_attribute_header; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE sample_attribute_header (
    id bigint,
    header character varying,
    num bigint
);


ALTER TABLE public.sample_attribute_header OWNER TO postgres;

--
-- Name: sample_attribute_header_sequence; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sample_attribute_header_sequence
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_attribute_header_sequence OWNER TO postgres;

--
-- Name: sample_attribute_sequence; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sample_attribute_sequence
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_attribute_sequence OWNER TO postgres;

--
-- Name: sample_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sample_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_id_seq OWNER TO postgres;

--
-- Name: sample_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE sample_id_seq OWNED BY sample.id;


--
-- Name: sample_tag; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE sample_tag (
    id integer NOT NULL,
    sample_id integer,
    series_tag_id integer,
    annotation text,
    is_active boolean NOT NULL,
    created_on timestamp without time zone,
    created_by integer,
    modified_on timestamp without time zone,
    modified_by integer
);


ALTER TABLE public.sample_tag OWNER TO postgres;

--
-- Name: sample_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sample_tag_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_tag_id_seq OWNER TO postgres;

--
-- Name: sample_tag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE sample_tag_id_seq OWNED BY sample_tag.id;


--
-- Name: sample_tag_sequence; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sample_tag_sequence
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_tag_sequence OWNER TO postgres;

--
-- Name: sample_tag_view_results; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE sample_tag_view_results (
    id integer NOT NULL,
    sample_tag_view_id integer,
    search_id integer
);


ALTER TABLE public.sample_tag_view_results OWNER TO postgres;

--
-- Name: sample_tag_view_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sample_tag_view_results_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_tag_view_results_id_seq OWNER TO postgres;

--
-- Name: sample_tag_view_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE sample_tag_view_results_id_seq OWNED BY sample_tag_view_results.id;


--
-- Name: sample_validation; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE sample_validation (
    id integer NOT NULL,
    annotation text NOT NULL,
    created_on timestamp with time zone NOT NULL,
    created_by_id integer NOT NULL,
    sample_id integer,
    serie_validation_id integer NOT NULL,
    concordant boolean
);


ALTER TABLE public.sample_validation OWNER TO postgres;

--
-- Name: sample_validation__backup; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE sample_validation__backup (
    id integer NOT NULL,
    annotation text NOT NULL,
    created_on timestamp with time zone NOT NULL,
    created_by_id integer NOT NULL,
    sample_id integer,
    serie_validation_id integer NOT NULL
);


ALTER TABLE public.sample_validation__backup OWNER TO postgres;

--
-- Name: sample_validation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sample_validation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_validation_id_seq OWNER TO postgres;

--
-- Name: sample_validation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE sample_validation_id_seq OWNED BY sample_validation.id;


--
-- Name: sample_view_annotation_filter; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE sample_view_annotation_filter (
    id integer NOT NULL,
    sample_view_id integer,
    annotation text,
    session_id character varying(512),
    created_on timestamp without time zone
);


ALTER TABLE public.sample_view_annotation_filter OWNER TO postgres;

--
-- Name: sample_view_annotation_filter_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sample_view_annotation_filter_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_view_annotation_filter_id_seq OWNER TO postgres;

--
-- Name: sample_view_annotation_filter_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE sample_view_annotation_filter_id_seq OWNED BY sample_view_annotation_filter.id;


--
-- Name: sample_view_results; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE sample_view_results (
    id integer NOT NULL,
    sample_view_id integer,
    search_id integer
);


ALTER TABLE public.sample_view_results OWNER TO postgres;

--
-- Name: sample_view_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE sample_view_results_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sample_view_results_id_seq OWNER TO postgres;

--
-- Name: sample_view_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE sample_view_results_id_seq OWNED BY sample_view_results.id;


--
-- Name: scheduler_run; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE scheduler_run (
    id integer NOT NULL,
    task_id integer,
    status character varying(512),
    start_time timestamp without time zone,
    stop_time timestamp without time zone,
    run_output text,
    run_result text,
    traceback text,
    worker_name character varying(512)
);


ALTER TABLE public.scheduler_run OWNER TO postgres;

--
-- Name: scheduler_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE scheduler_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.scheduler_run_id_seq OWNER TO postgres;

--
-- Name: scheduler_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE scheduler_run_id_seq OWNED BY scheduler_run.id;


--
-- Name: scheduler_task; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE scheduler_task (
    id integer NOT NULL,
    application_name character varying(512),
    task_name character varying(512),
    group_name character varying(512),
    status character varying(512),
    function_name character varying(512),
    uuid character varying(255),
    args text,
    vars text,
    enabled character(1),
    start_time timestamp without time zone,
    next_run_time timestamp without time zone,
    stop_time timestamp without time zone,
    repeats integer,
    retry_failed integer,
    period integer,
    prevent_drift character(1),
    timeout integer,
    sync_output integer,
    times_run integer,
    times_failed integer,
    last_run_time timestamp without time zone,
    assigned_worker_name character varying(512)
);


ALTER TABLE public.scheduler_task OWNER TO postgres;

--
-- Name: scheduler_task_deps; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE scheduler_task_deps (
    id integer NOT NULL,
    job_name character varying(512),
    task_parent integer,
    task_child integer,
    can_visit character(1)
);


ALTER TABLE public.scheduler_task_deps OWNER TO postgres;

--
-- Name: scheduler_task_deps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE scheduler_task_deps_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.scheduler_task_deps_id_seq OWNER TO postgres;

--
-- Name: scheduler_task_deps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE scheduler_task_deps_id_seq OWNED BY scheduler_task_deps.id;


--
-- Name: scheduler_task_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE scheduler_task_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.scheduler_task_id_seq OWNER TO postgres;

--
-- Name: scheduler_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE scheduler_task_id_seq OWNED BY scheduler_task.id;


--
-- Name: scheduler_worker; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE scheduler_worker (
    id integer NOT NULL,
    worker_name character varying(255),
    first_heartbeat timestamp without time zone,
    last_heartbeat timestamp without time zone,
    status character varying(512),
    is_ticker character(1),
    group_names text,
    worker_stats json
);


ALTER TABLE public.scheduler_worker OWNER TO postgres;

--
-- Name: scheduler_worker_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE scheduler_worker_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.scheduler_worker_id_seq OWNER TO postgres;

--
-- Name: scheduler_worker_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE scheduler_worker_id_seq OWNED BY scheduler_worker.id;


--
-- Name: search; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE search (
    id integer NOT NULL,
    fts_query character varying(512)
);


ALTER TABLE public.search OWNER TO postgres;

--
-- Name: search_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE search_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.search_id_seq OWNER TO postgres;

--
-- Name: search_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE search_id_seq OWNED BY search.id;


--
-- Name: series; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE series (
    id integer NOT NULL,
    gse_name text,
    attrs text NOT NULL,
    tsv tsvector,
    specie character varying(127) NOT NULL,
    platforms character varying(127)[] NOT NULL,
    samples_count integer NOT NULL
);


ALTER TABLE public.series OWNER TO postgres;

--
-- Name: series_annotation; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE series_annotation (
    id integer NOT NULL,
    header character varying(512) NOT NULL,
    regex character varying(512) NOT NULL,
    created_on timestamp with time zone,
    modified_on timestamp with time zone,
    annotations integer NOT NULL,
    authors integer NOT NULL,
    fleiss_kappa double precision,
    best_cohens_kappa double precision,
    platform_id integer,
    series_id integer,
    series_tag_id integer NOT NULL,
    tag_id integer,
    samples integer NOT NULL,
    captive boolean NOT NULL
);


ALTER TABLE public.series_annotation OWNER TO postgres;

--
-- Name: series_annotation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE series_annotation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.series_annotation_id_seq OWNER TO postgres;

--
-- Name: series_annotation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE series_annotation_id_seq OWNED BY series_annotation.id;


--
-- Name: series_attribute_header; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE series_attribute_header (
    id bigint,
    header text
);


ALTER TABLE public.series_attribute_header OWNER TO postgres;

--
-- Name: series_attribute_header_sequence; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE series_attribute_header_sequence
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.series_attribute_header_sequence OWNER TO postgres;

--
-- Name: series_attribute_sequence; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE series_attribute_sequence
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.series_attribute_sequence OWNER TO postgres;

--
-- Name: series_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE series_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.series_id_seq OWNER TO postgres;

--
-- Name: series_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE series_id_seq OWNED BY series.id;


--
-- Name: series_tag; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE series_tag (
    id integer NOT NULL,
    series_id integer,
    platform_id integer,
    tag_id integer,
    header character varying(512),
    regex character varying(512),
    is_active boolean NOT NULL,
    created_on timestamp without time zone,
    created_by integer,
    modified_on timestamp without time zone,
    modified_by integer,
    agreed integer,
    fleiss_kappa double precision,
    note text NOT NULL,
    from_api boolean NOT NULL
);


ALTER TABLE public.series_tag OWNER TO postgres;

--
-- Name: series_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE series_tag_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.series_tag_id_seq OWNER TO postgres;

--
-- Name: series_tag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE series_tag_id_seq OWNED BY series_tag.id;


--
-- Name: series_tag_sequence; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE series_tag_sequence
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.series_tag_sequence OWNER TO postgres;

--
-- Name: series_tag_view_results; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE series_tag_view_results (
    id integer NOT NULL,
    series_tag_view_id integer,
    search_id integer
);


ALTER TABLE public.series_tag_view_results OWNER TO postgres;

--
-- Name: series_tag_view_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE series_tag_view_results_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.series_tag_view_results_id_seq OWNER TO postgres;

--
-- Name: series_tag_view_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE series_tag_view_results_id_seq OWNED BY series_tag_view_results.id;


--
-- Name: series_validation; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE series_validation (
    id integer NOT NULL,
    "column" character varying(512) NOT NULL,
    regex character varying(512) NOT NULL,
    created_on timestamp with time zone NOT NULL,
    created_by_id integer NOT NULL,
    platform_id integer NOT NULL,
    series_id integer NOT NULL,
    series_tag_id integer,
    tag_id integer NOT NULL,
    samples_concordant integer,
    samples_total integer,
    agrees_with_id integer,
    annotation_kappa double precision,
    best_kappa double precision,
    on_demand boolean NOT NULL,
    ignored boolean NOT NULL,
    by_incompetent boolean NOT NULL,
    note text NOT NULL,
    from_api boolean NOT NULL
);


ALTER TABLE public.series_validation OWNER TO postgres;

--
-- Name: series_validation_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE series_validation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.series_validation_id_seq OWNER TO postgres;

--
-- Name: series_validation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE series_validation_id_seq OWNED BY series_validation.id;


--
-- Name: series_view_results; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE series_view_results (
    id integer NOT NULL,
    series_view_id integer,
    search_id integer
);


ALTER TABLE public.series_view_results OWNER TO postgres;

--
-- Name: series_view_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE series_view_results_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.series_view_results_id_seq OWNER TO postgres;

--
-- Name: series_view_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE series_view_results_id_seq OWNED BY series_view_results.id;


--
-- Name: snapshot; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE snapshot (
    id integer NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    metadata text NOT NULL,
    created_on timestamp with time zone NOT NULL,
    modified_on timestamp with time zone NOT NULL,
    frozen boolean NOT NULL,
    frozen_on timestamp with time zone,
    files text NOT NULL,
    author_id integer NOT NULL
);


ALTER TABLE public.snapshot OWNER TO postgres;

--
-- Name: snapshot_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE snapshot_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.snapshot_id_seq OWNER TO postgres;

--
-- Name: snapshot_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE snapshot_id_seq OWNED BY snapshot.id;


--
-- Name: tag; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tag (
    id integer NOT NULL,
    tag_name character varying(512),
    description character varying(512),
    is_active boolean NOT NULL,
    created_on timestamp without time zone,
    created_by integer,
    modified_on timestamp without time zone,
    modified_by integer,
    concept_full_id character varying(512) NOT NULL,
    concept_name character varying(512) NOT NULL,
    ontology_id character varying(127) NOT NULL
);


ALTER TABLE public.tag OWNER TO postgres;

--
-- Name: tag_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tag_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tag_id_seq OWNER TO postgres;

--
-- Name: tag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE tag_id_seq OWNED BY tag.id;


--
-- Name: tags_payment; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tags_payment (
    id integer NOT NULL,
    amount numeric(8,2) NOT NULL,
    method text NOT NULL,
    created_on timestamp with time zone NOT NULL,
    created_by_id integer NOT NULL,
    receiver_id integer NOT NULL,
    extra text NOT NULL,
    state integer NOT NULL
);


ALTER TABLE public.tags_payment OWNER TO postgres;

--
-- Name: tags_payment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tags_payment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tags_payment_id_seq OWNER TO postgres;

--
-- Name: tags_payment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE tags_payment_id_seq OWNED BY tags_payment.id;


--
-- Name: tags_userstats; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tags_userstats (
    user_id integer NOT NULL,
    serie_tags integer NOT NULL,
    sample_tags integer NOT NULL,
    serie_validations integer NOT NULL,
    sample_validations integer NOT NULL,
    serie_validations_concordant integer NOT NULL,
    sample_validations_concordant integer NOT NULL,
    earned_sample_annotations integer NOT NULL,
    earned numeric(8,2) NOT NULL,
    earned_sample_validations integer NOT NULL,
    payed numeric(8,2) NOT NULL
);


ALTER TABLE public.tags_userstats OWNER TO postgres;

--
-- Name: user_search; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE user_search (
    id integer NOT NULL,
    search_id integer,
    keywords character varying(512),
    is_active character(1),
    created_on timestamp without time zone,
    created_by integer,
    modified_on timestamp without time zone,
    modified_by integer,
    fts_query character varying(512)
);


ALTER TABLE public.user_search OWNER TO postgres;

--
-- Name: user_search_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE user_search_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_search_id_seq OWNER TO postgres;

--
-- Name: user_search_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE user_search_id_seq OWNED BY user_search.id;


--
-- Name: validation_job; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE validation_job (
    id integer NOT NULL,
    locked_on timestamp with time zone,
    locked_by_id integer,
    series_tag_id integer NOT NULL,
    priority double precision NOT NULL
);


ALTER TABLE public.validation_job OWNER TO postgres;

--
-- Name: validation_job_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE validation_job_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.validation_job_id_seq OWNER TO postgres;

--
-- Name: validation_job_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE validation_job_id_seq OWNED BY validation_job.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY analysis ALTER COLUMN id SET DEFAULT nextval('analysis_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_group ALTER COLUMN id SET DEFAULT nextval('dauth_group_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_group_permissions ALTER COLUMN id SET DEFAULT nextval('dauth_group_permissions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_permission ALTER COLUMN id SET DEFAULT nextval('dauth_permission_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user ALTER COLUMN id SET DEFAULT nextval('dauth_user_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_groups ALTER COLUMN id SET DEFAULT nextval('dauth_user_groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_user_permissions ALTER COLUMN id SET DEFAULT nextval('dauth_user_user_permissions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY balanced_meta ALTER COLUMN id SET DEFAULT nextval('balanced_meta_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY core_statisticcache ALTER COLUMN id SET DEFAULT nextval('core_statisticcache_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY count ALTER COLUMN id SET DEFAULT nextval('count_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_admin_log ALTER COLUMN id SET DEFAULT nextval('django_admin_log_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_content_type ALTER COLUMN id SET DEFAULT nextval('django_content_type_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_migrations ALTER COLUMN id SET DEFAULT nextval('django_migrations_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY meta_analysis ALTER COLUMN id SET DEFAULT nextval('meta_analysis_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY platform ALTER COLUMN id SET DEFAULT nextval('platform_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY platform_probe ALTER COLUMN id SET DEFAULT nextval('platform_probe_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample ALTER COLUMN id SET DEFAULT nextval('sample_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_annotation ALTER COLUMN id SET DEFAULT nextval('sample_annotation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_tag ALTER COLUMN id SET DEFAULT nextval('sample_tag_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_tag_view_results ALTER COLUMN id SET DEFAULT nextval('sample_tag_view_results_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_validation ALTER COLUMN id SET DEFAULT nextval('sample_validation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_view_annotation_filter ALTER COLUMN id SET DEFAULT nextval('sample_view_annotation_filter_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_view_results ALTER COLUMN id SET DEFAULT nextval('sample_view_results_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY scheduler_run ALTER COLUMN id SET DEFAULT nextval('scheduler_run_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY scheduler_task ALTER COLUMN id SET DEFAULT nextval('scheduler_task_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY scheduler_task_deps ALTER COLUMN id SET DEFAULT nextval('scheduler_task_deps_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY scheduler_worker ALTER COLUMN id SET DEFAULT nextval('scheduler_worker_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY search ALTER COLUMN id SET DEFAULT nextval('search_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series ALTER COLUMN id SET DEFAULT nextval('series_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_annotation ALTER COLUMN id SET DEFAULT nextval('series_annotation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_tag ALTER COLUMN id SET DEFAULT nextval('series_tag_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_tag_view_results ALTER COLUMN id SET DEFAULT nextval('series_tag_view_results_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_validation ALTER COLUMN id SET DEFAULT nextval('series_validation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_view_results ALTER COLUMN id SET DEFAULT nextval('series_view_results_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY snapshot ALTER COLUMN id SET DEFAULT nextval('snapshot_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tag ALTER COLUMN id SET DEFAULT nextval('tag_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tags_payment ALTER COLUMN id SET DEFAULT nextval('tags_payment_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY user_search ALTER COLUMN id SET DEFAULT nextval('user_search_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY validation_job ALTER COLUMN id SET DEFAULT nextval('validation_job_id_seq'::regclass);


--
-- Name: analysis_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY analysis
    ADD CONSTRAINT analysis_pkey PRIMARY KEY (id);


--
-- Name: authtoken_token_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY authtoken_token
    ADD CONSTRAINT authtoken_token_pkey PRIMARY KEY (key);


--
-- Name: authtoken_token_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY authtoken_token
    ADD CONSTRAINT authtoken_token_user_id_key UNIQUE (user_id);


--
-- Name: balanced_meta_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY balanced_meta
    ADD CONSTRAINT balanced_meta_pkey PRIMARY KEY (id);


--
-- Name: core_statisticcache_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY core_statisticcache
    ADD CONSTRAINT core_statisticcache_pkey PRIMARY KEY (id);


--
-- Name: core_statisticcache_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY core_statisticcache
    ADD CONSTRAINT core_statisticcache_slug_key UNIQUE (slug);


--
-- Name: count_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY count
    ADD CONSTRAINT count_pkey PRIMARY KEY (id);


--
-- Name: dauth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT dauth_group_name_key UNIQUE (name);


--
-- Name: dauth_group_permissions_group_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT dauth_group_permissions_group_id_permission_id_key UNIQUE (group_id, permission_id);


--
-- Name: dauth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT dauth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: dauth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_group
    ADD CONSTRAINT dauth_group_pkey PRIMARY KEY (id);


--
-- Name: dauth_permission_content_type_id_f690643cacb0e35_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT dauth_permission_content_type_id_f690643cacb0e35_uniq UNIQUE (content_type_id, codename);


--
-- Name: dauth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT dauth_permission_pkey PRIMARY KEY (id);


--
-- Name: dauth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT dauth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: dauth_user_groups_user_id_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT dauth_user_groups_user_id_group_id_key UNIQUE (user_id, group_id);


--
-- Name: dauth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user
    ADD CONSTRAINT dauth_user_pkey PRIMARY KEY (id);


--
-- Name: dauth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT dauth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: dauth_user_user_permissions_user_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT dauth_user_user_permissions_user_id_permission_id_key UNIQUE (user_id, permission_id);


--
-- Name: dauth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY auth_user
    ADD CONSTRAINT dauth_user_username_key UNIQUE (username);


--
-- Name: django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type_app_label_45f3b1d93ec8c61c_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_app_label_45f3b1d93ec8c61c_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: meta_analysis_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY meta_analysis
    ADD CONSTRAINT meta_analysis_pkey PRIMARY KEY (id);


--
-- Name: platform_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY platform
    ADD CONSTRAINT platform_pkey PRIMARY KEY (id);


--
-- Name: platform_probe_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY platform_probe
    ADD CONSTRAINT platform_probe_pkey PRIMARY KEY (id);


--
-- Name: sample_annotation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY sample_annotation
    ADD CONSTRAINT sample_annotation_pkey PRIMARY KEY (id);


--
-- Name: sample_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY sample
    ADD CONSTRAINT sample_pkey PRIMARY KEY (id);


--
-- Name: sample_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY sample_tag
    ADD CONSTRAINT sample_tag_pkey PRIMARY KEY (id);


--
-- Name: sample_tag_view_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY sample_tag_view_results
    ADD CONSTRAINT sample_tag_view_results_pkey PRIMARY KEY (id);


--
-- Name: sample_validation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY sample_validation
    ADD CONSTRAINT sample_validation_pkey PRIMARY KEY (id);


--
-- Name: sample_view_annotation_filter_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY sample_view_annotation_filter
    ADD CONSTRAINT sample_view_annotation_filter_pkey PRIMARY KEY (id);


--
-- Name: sample_view_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY sample_view_results
    ADD CONSTRAINT sample_view_results_pkey PRIMARY KEY (id);


--
-- Name: scheduler_run_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY scheduler_run
    ADD CONSTRAINT scheduler_run_pkey PRIMARY KEY (id);


--
-- Name: scheduler_task_deps_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY scheduler_task_deps
    ADD CONSTRAINT scheduler_task_deps_pkey PRIMARY KEY (id);


--
-- Name: scheduler_task_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY scheduler_task
    ADD CONSTRAINT scheduler_task_pkey PRIMARY KEY (id);


--
-- Name: scheduler_task_uuid_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY scheduler_task
    ADD CONSTRAINT scheduler_task_uuid_key UNIQUE (uuid);


--
-- Name: scheduler_worker_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY scheduler_worker
    ADD CONSTRAINT scheduler_worker_pkey PRIMARY KEY (id);


--
-- Name: scheduler_worker_worker_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY scheduler_worker
    ADD CONSTRAINT scheduler_worker_worker_name_key UNIQUE (worker_name);


--
-- Name: search_fts_query_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY search
    ADD CONSTRAINT search_fts_query_key UNIQUE (fts_query);


--
-- Name: search_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY search
    ADD CONSTRAINT search_pkey PRIMARY KEY (id);


--
-- Name: series_annotation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY series_annotation
    ADD CONSTRAINT series_annotation_pkey PRIMARY KEY (id);


--
-- Name: series_annotation_series_tag_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY series_annotation
    ADD CONSTRAINT series_annotation_series_tag_id_key UNIQUE (series_tag_id);


--
-- Name: series_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY series
    ADD CONSTRAINT series_pkey PRIMARY KEY (id);


--
-- Name: series_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY series_tag
    ADD CONSTRAINT series_tag_pkey PRIMARY KEY (id);


--
-- Name: series_tag_view_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY series_tag_view_results
    ADD CONSTRAINT series_tag_view_results_pkey PRIMARY KEY (id);


--
-- Name: series_validation_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY series_validation
    ADD CONSTRAINT series_validation_pkey PRIMARY KEY (id);


--
-- Name: series_view_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY series_view_results
    ADD CONSTRAINT series_view_results_pkey PRIMARY KEY (id);


--
-- Name: snapshot_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY snapshot
    ADD CONSTRAINT snapshot_pkey PRIMARY KEY (id);


--
-- Name: tag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tag
    ADD CONSTRAINT tag_pkey PRIMARY KEY (id);


--
-- Name: tags_payment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tags_payment
    ADD CONSTRAINT tags_payment_pkey PRIMARY KEY (id);


--
-- Name: tags_userstats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tags_userstats
    ADD CONSTRAINT tags_userstats_pkey PRIMARY KEY (user_id);


--
-- Name: user_search_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY user_search
    ADD CONSTRAINT user_search_pkey PRIMARY KEY (id);


--
-- Name: validation_job_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY validation_job
    ADD CONSTRAINT validation_job_pkey PRIMARY KEY (id);


--
-- Name: authtoken_token_key_7222ec672cd32dcd_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX authtoken_token_key_7222ec672cd32dcd_like ON authtoken_token USING btree (key varchar_pattern_ops);


--
-- Name: core_statisticcache_slug_7ea2ea5e536156bf_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX core_statisticcache_slug_7ea2ea5e536156bf_like ON core_statisticcache USING btree (slug varchar_pattern_ops);


--
-- Name: dauth_group_name_5df72905594de2d7_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dauth_group_name_5df72905594de2d7_like ON auth_group USING btree (name varchar_pattern_ops);


--
-- Name: dauth_group_permissions_0e939a4f; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dauth_group_permissions_0e939a4f ON auth_group_permissions USING btree (group_id);


--
-- Name: dauth_group_permissions_8373b171; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dauth_group_permissions_8373b171 ON auth_group_permissions USING btree (permission_id);


--
-- Name: dauth_permission_417f1b1c; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dauth_permission_417f1b1c ON auth_permission USING btree (content_type_id);


--
-- Name: dauth_user_groups_0e939a4f; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dauth_user_groups_0e939a4f ON auth_user_groups USING btree (group_id);


--
-- Name: dauth_user_groups_e8701ad4; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dauth_user_groups_e8701ad4 ON auth_user_groups USING btree (user_id);


--
-- Name: dauth_user_user_permissions_8373b171; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dauth_user_user_permissions_8373b171 ON auth_user_user_permissions USING btree (permission_id);


--
-- Name: dauth_user_user_permissions_e8701ad4; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dauth_user_user_permissions_e8701ad4 ON auth_user_user_permissions USING btree (user_id);


--
-- Name: dauth_user_username_635c123e9e50f35b_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX dauth_user_username_635c123e9e50f35b_like ON auth_user USING btree (username varchar_pattern_ops);


--
-- Name: django_admin_log_417f1b1c; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_admin_log_417f1b1c ON django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_e8701ad4; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_admin_log_e8701ad4 ON django_admin_log USING btree (user_id);


--
-- Name: django_session_de54fa62; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_session_de54fa62 ON django_session USING btree (expire_date);


--
-- Name: django_session_session_key_461cfeaa630ca218_like; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX django_session_session_key_461cfeaa630ca218_like ON django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: meta_analysis_analysis_id_670b330a4802bb59_uniq; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX meta_analysis_analysis_id_670b330a4802bb59_uniq ON meta_analysis USING btree (analysis_id);


--
-- Name: platform_gpl_name_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE UNIQUE INDEX platform_gpl_name_idx ON platform USING btree (gpl_name);


--
-- Name: platformprobe_platformid_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX platformprobe_platformid_idx ON platform_probe USING btree (platform_id);


--
-- Name: sample_annotation_a00c0364; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX sample_annotation_a00c0364 ON sample_annotation USING btree (serie_annotation_id);


--
-- Name: sample_annotation_c09c8085; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX sample_annotation_c09c8085 ON sample_annotation USING btree (sample_id);


--
-- Name: sample_series_id_f2643d84d9b52bd_uniq; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX sample_series_id_f2643d84d9b52bd_uniq ON sample USING btree (series_id);


--
-- Name: sample_validation_119e48fc; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX sample_validation_119e48fc ON sample_validation USING btree (serie_validation_id);


--
-- Name: sample_validation_c09c8085; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX sample_validation_c09c8085 ON sample_validation USING btree (sample_id);


--
-- Name: sample_validation_e93cb7eb; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX sample_validation_e93cb7eb ON sample_validation USING btree (created_by_id);


--
-- Name: sampletag_sampleid_seriestagid_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE UNIQUE INDEX sampletag_sampleid_seriestagid_idx ON sample_tag USING btree (sample_id, series_tag_id);


--
-- Name: series_annotation_76f094bc; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX series_annotation_76f094bc ON series_annotation USING btree (tag_id);


--
-- Name: series_annotation_a08cee2d; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX series_annotation_a08cee2d ON series_annotation USING btree (series_id);


--
-- Name: series_annotation_cb857215; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX series_annotation_cb857215 ON series_annotation USING btree (platform_id);


--
-- Name: series_gse_name_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE UNIQUE INDEX series_gse_name_idx ON series USING btree (gse_name);


--
-- Name: series_search_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX series_search_idx ON series USING gist (tsv);


--
-- Name: series_validation_76f094bc; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX series_validation_76f094bc ON series_validation USING btree (tag_id);


--
-- Name: series_validation_a08cee2d; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX series_validation_a08cee2d ON series_validation USING btree (series_id);


--
-- Name: series_validation_a0ed57d9; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX series_validation_a0ed57d9 ON series_validation USING btree (series_tag_id);


--
-- Name: series_validation_cb857215; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX series_validation_cb857215 ON series_validation USING btree (platform_id);


--
-- Name: series_validation_d7111d83; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX series_validation_d7111d83 ON series_validation USING btree (agrees_with_id);


--
-- Name: series_validation_e93cb7eb; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX series_validation_e93cb7eb ON series_validation USING btree (created_by_id);


--
-- Name: snapshot_4f331e2f; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX snapshot_4f331e2f ON snapshot USING btree (author_id);


--
-- Name: tag_name_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE UNIQUE INDEX tag_name_idx ON tag USING btree (tag_name) WHERE is_active;


--
-- Name: tags_payment_d41c2251; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX tags_payment_d41c2251 ON tags_payment USING btree (receiver_id);


--
-- Name: tags_payment_e93cb7eb; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX tags_payment_e93cb7eb ON tags_payment USING btree (created_by_id);


--
-- Name: validation_job_36d90bd2; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX validation_job_36d90bd2 ON validation_job USING btree (locked_by_id);


--
-- Name: validation_job_a0ed57d9; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX validation_job_a0ed57d9 ON validation_job USING btree (series_tag_id);


--
-- Name: update_tsv; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_tsv BEFORE INSERT OR UPDATE ON series FOR EACH ROW EXECUTE PROCEDURE make_attrs_tsv();


--
-- Name: analysis_created_by_fe12d412ea74337_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY analysis
    ADD CONSTRAINT analysis_created_by_fe12d412ea74337_fk_dauth_user_id FOREIGN KEY (created_by) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: analysis_modified_by_13b47b2a97368d89_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY analysis
    ADD CONSTRAINT analysis_modified_by_13b47b2a97368d89_fk_dauth_user_id FOREIGN KEY (modified_by) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: authtoken_token_user_id_1d10c57f535fb363_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY authtoken_token
    ADD CONSTRAINT authtoken_token_user_id_1d10c57f535fb363_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: balanced_meta_analysis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY balanced_meta
    ADD CONSTRAINT balanced_meta_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES analysis(id) ON DELETE CASCADE;


--
-- Name: dauth_content_type_id_ea8a9d7172f5d7c_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_permission
    ADD CONSTRAINT dauth_content_type_id_ea8a9d7172f5d7c_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dauth_gro_permission_id_6588ad254c950e73_fk_dauth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT dauth_gro_permission_id_6588ad254c950e73_fk_dauth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dauth_group_permiss_group_id_6508e6b0fe5ffb66_fk_dauth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_group_permissions
    ADD CONSTRAINT dauth_group_permiss_group_id_6508e6b0fe5ffb66_fk_dauth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dauth_use_permission_id_355e7116341c99b1_fk_dauth_permission_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT dauth_use_permission_id_355e7116341c99b1_fk_dauth_permission_id FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dauth_user_groups_group_id_807e6f775df346c_fk_dauth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT dauth_user_groups_group_id_807e6f775df346c_fk_dauth_group_id FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dauth_user_groups_user_id_30eb6785536728f3_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_groups
    ADD CONSTRAINT dauth_user_groups_user_id_30eb6785536728f3_fk_dauth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: dauth_user_user_permi_user_id_7696a5e2350d7ae5_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY auth_user_user_permissions
    ADD CONSTRAINT dauth_user_user_permi_user_id_7696a5e2350d7ae5_fk_dauth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: djan_content_type_id_697914295151027a_fk_django_content_type_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT djan_content_type_id_697914295151027a_fk_django_content_type_id FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log_user_id_52fdd58701c5f563_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_52fdd58701c5f563_fk_dauth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: meta_analysis_analysis_id_670b330a4802bb59_fk_analysis_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY meta_analysis
    ADD CONSTRAINT meta_analysis_analysis_id_670b330a4802bb59_fk_analysis_id FOREIGN KEY (analysis_id) REFERENCES analysis(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: platform_probe_platform_id_6a88785d3abfaf71_fk_platform_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY platform_probe
    ADD CONSTRAINT platform_probe_platform_id_6a88785d3abfaf71_fk_platform_id FOREIGN KEY (platform_id) REFERENCES platform(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sa_serie_annotation_id_18709afba68c3479_fk_series_annotation_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_annotation
    ADD CONSTRAINT sa_serie_annotation_id_18709afba68c3479_fk_series_annotation_id FOREIGN KEY (serie_annotation_id) REFERENCES series_annotation(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sa_serie_validation_id_6052500a1209f723_fk_series_validation_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_validation
    ADD CONSTRAINT sa_serie_validation_id_6052500a1209f723_fk_series_validation_id FOREIGN KEY (serie_validation_id) REFERENCES series_validation(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sample_annotation_sample_id_52afa0cb335b7911_fk_sample_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_annotation
    ADD CONSTRAINT sample_annotation_sample_id_52afa0cb335b7911_fk_sample_id FOREIGN KEY (sample_id) REFERENCES sample(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sample_platform_id_68fc4def4d2d2cdd_fk_platform_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample
    ADD CONSTRAINT sample_platform_id_68fc4def4d2d2cdd_fk_platform_id FOREIGN KEY (platform_id) REFERENCES platform(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sample_series_id_f2643d84d9b52bd_fk_series_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample
    ADD CONSTRAINT sample_series_id_f2643d84d9b52bd_fk_series_id FOREIGN KEY (series_id) REFERENCES series(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sample_tag_created_by_4adad53fd1a570c0_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_tag
    ADD CONSTRAINT sample_tag_created_by_4adad53fd1a570c0_fk_dauth_user_id FOREIGN KEY (created_by) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sample_tag_modified_by_4e0b5ea5e8d938ee_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_tag
    ADD CONSTRAINT sample_tag_modified_by_4e0b5ea5e8d938ee_fk_dauth_user_id FOREIGN KEY (modified_by) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sample_tag_sample_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_tag
    ADD CONSTRAINT sample_tag_sample_id_fkey FOREIGN KEY (sample_id) REFERENCES sample(id) ON DELETE CASCADE;


--
-- Name: sample_tag_series_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_tag
    ADD CONSTRAINT sample_tag_series_tag_id_fkey FOREIGN KEY (series_tag_id) REFERENCES series_tag(id) ON DELETE CASCADE;


--
-- Name: sample_tag_view_results_search_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_tag_view_results
    ADD CONSTRAINT sample_tag_view_results_search_id_fkey FOREIGN KEY (search_id) REFERENCES search(id) ON DELETE CASCADE;


--
-- Name: sample_validati_created_by_id_75ca08cba9e0257d_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_validation
    ADD CONSTRAINT sample_validati_created_by_id_75ca08cba9e0257d_fk_dauth_user_id FOREIGN KEY (created_by_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sample_validation_sample_id_7d362a9b0eabbb6f_fk_sample_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_validation
    ADD CONSTRAINT sample_validation_sample_id_7d362a9b0eabbb6f_fk_sample_id FOREIGN KEY (sample_id) REFERENCES sample(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: sample_view_results_search_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY sample_view_results
    ADD CONSTRAINT sample_view_results_search_id_fkey FOREIGN KEY (search_id) REFERENCES search(id) ON DELETE CASCADE;


--
-- Name: scheduler_run_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY scheduler_run
    ADD CONSTRAINT scheduler_run_task_id_fkey FOREIGN KEY (task_id) REFERENCES scheduler_task(id) ON DELETE CASCADE;


--
-- Name: scheduler_task_deps_task_child_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY scheduler_task_deps
    ADD CONSTRAINT scheduler_task_deps_task_child_fkey FOREIGN KEY (task_child) REFERENCES scheduler_task(id) ON DELETE CASCADE;


--
-- Name: series_annotati_series_tag_id_523d6713ae1132e2_fk_series_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_annotation
    ADD CONSTRAINT series_annotati_series_tag_id_523d6713ae1132e2_fk_series_tag_id FOREIGN KEY (series_tag_id) REFERENCES series_tag(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: series_annotation_platform_id_699f5ca3d39d4599_fk_platform_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_annotation
    ADD CONSTRAINT series_annotation_platform_id_699f5ca3d39d4599_fk_platform_id FOREIGN KEY (platform_id) REFERENCES platform(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: series_annotation_series_id_5dcb4fb05ad04487_fk_series_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_annotation
    ADD CONSTRAINT series_annotation_series_id_5dcb4fb05ad04487_fk_series_id FOREIGN KEY (series_id) REFERENCES series(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: series_annotation_tag_id_2d1adff958d84deb_fk_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_annotation
    ADD CONSTRAINT series_annotation_tag_id_2d1adff958d84deb_fk_tag_id FOREIGN KEY (tag_id) REFERENCES tag(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: series_tag_created_by_5761d5f56c4f71cf_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_tag
    ADD CONSTRAINT series_tag_created_by_5761d5f56c4f71cf_fk_dauth_user_id FOREIGN KEY (created_by) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: series_tag_modified_by_1d68ea002f42e0f_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_tag
    ADD CONSTRAINT series_tag_modified_by_1d68ea002f42e0f_fk_dauth_user_id FOREIGN KEY (modified_by) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: series_tag_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_tag
    ADD CONSTRAINT series_tag_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES platform(id) ON DELETE CASCADE;


--
-- Name: series_tag_series_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_tag
    ADD CONSTRAINT series_tag_series_id_fkey FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE;


--
-- Name: series_tag_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_tag
    ADD CONSTRAINT series_tag_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE;


--
-- Name: series_tag_view_results_search_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_tag_view_results
    ADD CONSTRAINT series_tag_view_results_search_id_fkey FOREIGN KEY (search_id) REFERENCES search(id) ON DELETE CASCADE;


--
-- Name: series_v_agrees_with_id_f892f9ac8d10447_fk_series_validation_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_validation
    ADD CONSTRAINT series_v_agrees_with_id_f892f9ac8d10447_fk_series_validation_id FOREIGN KEY (agrees_with_id) REFERENCES series_validation(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: series_validati_created_by_id_5a5f4e76ccf95bb2_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_validation
    ADD CONSTRAINT series_validati_created_by_id_5a5f4e76ccf95bb2_fk_dauth_user_id FOREIGN KEY (created_by_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: series_validati_series_tag_id_5a35d6201a93f3ec_fk_series_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_validation
    ADD CONSTRAINT series_validati_series_tag_id_5a35d6201a93f3ec_fk_series_tag_id FOREIGN KEY (series_tag_id) REFERENCES series_tag(id) ON DELETE SET NULL;


--
-- Name: series_validation_platform_id_3a87da320c5df303_fk_platform_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_validation
    ADD CONSTRAINT series_validation_platform_id_3a87da320c5df303_fk_platform_id FOREIGN KEY (platform_id) REFERENCES platform(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: series_validation_series_id_3ce2300ecf3f4023_fk_series_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_validation
    ADD CONSTRAINT series_validation_series_id_3ce2300ecf3f4023_fk_series_id FOREIGN KEY (series_id) REFERENCES series(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: series_validation_tag_id_25b442171edac81_fk_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_validation
    ADD CONSTRAINT series_validation_tag_id_25b442171edac81_fk_tag_id FOREIGN KEY (tag_id) REFERENCES tag(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: series_view_results_search_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY series_view_results
    ADD CONSTRAINT series_view_results_search_id_fkey FOREIGN KEY (search_id) REFERENCES search(id) ON DELETE CASCADE;


--
-- Name: snapshot_author_id_5e7b968bf22f65f_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY snapshot
    ADD CONSTRAINT snapshot_author_id_5e7b968bf22f65f_fk_auth_user_id FOREIGN KEY (author_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: tag_created_by_598a0a7ceea87c4e_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tag
    ADD CONSTRAINT tag_created_by_598a0a7ceea87c4e_fk_dauth_user_id FOREIGN KEY (created_by) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: tag_modified_by_4f9d87f962761c2c_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tag
    ADD CONSTRAINT tag_modified_by_4f9d87f962761c2c_fk_dauth_user_id FOREIGN KEY (modified_by) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: tags_payment_created_by_id_50a1bdc493020b44_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tags_payment
    ADD CONSTRAINT tags_payment_created_by_id_50a1bdc493020b44_fk_dauth_user_id FOREIGN KEY (created_by_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: tags_payment_receiver_id_5a03ce2ba64d3dc9_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tags_payment
    ADD CONSTRAINT tags_payment_receiver_id_5a03ce2ba64d3dc9_fk_dauth_user_id FOREIGN KEY (receiver_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: tags_userstats_user_id_7feba5a94e8a112b_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tags_userstats
    ADD CONSTRAINT tags_userstats_user_id_7feba5a94e8a112b_fk_dauth_user_id FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: user_search_search_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY user_search
    ADD CONSTRAINT user_search_search_id_fkey FOREIGN KEY (search_id) REFERENCES search(id) ON DELETE CASCADE;


--
-- Name: validation_job_locked_by_id_4266817ff1ad2262_fk_dauth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY validation_job
    ADD CONSTRAINT validation_job_locked_by_id_4266817ff1ad2262_fk_dauth_user_id FOREIGN KEY (locked_by_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: validation_job_series_tag_id_753f178d05a7d70f_fk_series_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY validation_job
    ADD CONSTRAINT validation_job_series_tag_id_753f178d05a7d70f_fk_series_tag_id FOREIGN KEY (series_tag_id) REFERENCES series_tag(id) ON DELETE CASCADE;


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: concat_tsvectors(tsvector, tsvector); Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON FUNCTION concat_tsvectors(tsv1 tsvector, tsv2 tsvector) FROM PUBLIC;
REVOKE ALL ON FUNCTION concat_tsvectors(tsv1 tsvector, tsv2 tsvector) FROM postgres;
GRANT ALL ON FUNCTION concat_tsvectors(tsv1 tsvector, tsv2 tsvector) TO postgres;
GRANT ALL ON FUNCTION concat_tsvectors(tsv1 tsvector, tsv2 tsvector) TO PUBLIC;


--
-- Name: analysis; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE analysis FROM PUBLIC;
REVOKE ALL ON TABLE analysis FROM postgres;
GRANT ALL ON TABLE analysis TO postgres;


--
-- Name: balanced_meta; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE balanced_meta FROM PUBLIC;
REVOKE ALL ON TABLE balanced_meta FROM postgres;
GRANT ALL ON TABLE balanced_meta TO postgres;


--
-- Name: count; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE count FROM PUBLIC;
REVOKE ALL ON TABLE count FROM postgres;
GRANT ALL ON TABLE count TO postgres;


--
-- Name: django_migrations; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE django_migrations FROM PUBLIC;
REVOKE ALL ON TABLE django_migrations FROM postgres;
GRANT ALL ON TABLE django_migrations TO postgres;


--
-- Name: meta_analysis; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE meta_analysis FROM PUBLIC;
REVOKE ALL ON TABLE meta_analysis FROM postgres;
GRANT ALL ON TABLE meta_analysis TO postgres;


--
-- Name: platform; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE platform FROM PUBLIC;
REVOKE ALL ON TABLE platform FROM postgres;
GRANT ALL ON TABLE platform TO postgres;


--
-- Name: platform_probe; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE platform_probe FROM PUBLIC;
REVOKE ALL ON TABLE platform_probe FROM postgres;
GRANT ALL ON TABLE platform_probe TO postgres;


--
-- Name: sample; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE sample FROM PUBLIC;
REVOKE ALL ON TABLE sample FROM postgres;
GRANT ALL ON TABLE sample TO postgres;


--
-- Name: sample_tag; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE sample_tag FROM PUBLIC;
REVOKE ALL ON TABLE sample_tag FROM postgres;
GRANT ALL ON TABLE sample_tag TO postgres;


--
-- Name: sample_tag_view_results; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE sample_tag_view_results FROM PUBLIC;
REVOKE ALL ON TABLE sample_tag_view_results FROM postgres;
GRANT ALL ON TABLE sample_tag_view_results TO postgres;


--
-- Name: sample_validation; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE sample_validation FROM PUBLIC;
REVOKE ALL ON TABLE sample_validation FROM postgres;
GRANT ALL ON TABLE sample_validation TO postgres;


--
-- Name: sample_validation__backup; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE sample_validation__backup FROM PUBLIC;
REVOKE ALL ON TABLE sample_validation__backup FROM postgres;
GRANT ALL ON TABLE sample_validation__backup TO postgres;


--
-- Name: sample_view_annotation_filter; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE sample_view_annotation_filter FROM PUBLIC;
REVOKE ALL ON TABLE sample_view_annotation_filter FROM postgres;
GRANT ALL ON TABLE sample_view_annotation_filter TO postgres;


--
-- Name: sample_view_results; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE sample_view_results FROM PUBLIC;
REVOKE ALL ON TABLE sample_view_results FROM postgres;
GRANT ALL ON TABLE sample_view_results TO postgres;


--
-- Name: scheduler_run; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE scheduler_run FROM PUBLIC;
REVOKE ALL ON TABLE scheduler_run FROM postgres;
GRANT ALL ON TABLE scheduler_run TO postgres;


--
-- Name: scheduler_task; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE scheduler_task FROM PUBLIC;
REVOKE ALL ON TABLE scheduler_task FROM postgres;
GRANT ALL ON TABLE scheduler_task TO postgres;


--
-- Name: scheduler_task_deps; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE scheduler_task_deps FROM PUBLIC;
REVOKE ALL ON TABLE scheduler_task_deps FROM postgres;
GRANT ALL ON TABLE scheduler_task_deps TO postgres;


--
-- Name: scheduler_worker; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE scheduler_worker FROM PUBLIC;
REVOKE ALL ON TABLE scheduler_worker FROM postgres;
GRANT ALL ON TABLE scheduler_worker TO postgres;


--
-- Name: search; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE search FROM PUBLIC;
REVOKE ALL ON TABLE search FROM postgres;
GRANT ALL ON TABLE search TO postgres;


--
-- Name: series; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE series FROM PUBLIC;
REVOKE ALL ON TABLE series FROM postgres;
GRANT ALL ON TABLE series TO postgres;


--
-- Name: series_tag; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE series_tag FROM PUBLIC;
REVOKE ALL ON TABLE series_tag FROM postgres;
GRANT ALL ON TABLE series_tag TO postgres;


--
-- Name: series_tag_view_results; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE series_tag_view_results FROM PUBLIC;
REVOKE ALL ON TABLE series_tag_view_results FROM postgres;
GRANT ALL ON TABLE series_tag_view_results TO postgres;


--
-- Name: series_validation; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE series_validation FROM PUBLIC;
REVOKE ALL ON TABLE series_validation FROM postgres;
GRANT ALL ON TABLE series_validation TO postgres;


--
-- Name: series_view_results; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE series_view_results FROM PUBLIC;
REVOKE ALL ON TABLE series_view_results FROM postgres;
GRANT ALL ON TABLE series_view_results TO postgres;


--
-- Name: tag; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE tag FROM PUBLIC;
REVOKE ALL ON TABLE tag FROM postgres;
GRANT ALL ON TABLE tag TO postgres;


--
-- Name: tags_payment; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE tags_payment FROM PUBLIC;
REVOKE ALL ON TABLE tags_payment FROM postgres;
GRANT ALL ON TABLE tags_payment TO postgres;


--
-- Name: tags_userstats; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE tags_userstats FROM PUBLIC;
REVOKE ALL ON TABLE tags_userstats FROM postgres;
GRANT ALL ON TABLE tags_userstats TO postgres;


--
-- Name: user_search; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE user_search FROM PUBLIC;
REVOKE ALL ON TABLE user_search FROM postgres;
GRANT ALL ON TABLE user_search TO postgres;


--
-- Name: validation_job; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE validation_job FROM PUBLIC;
REVOKE ALL ON TABLE validation_job FROM postgres;
GRANT ALL ON TABLE validation_job TO postgres;


--
-- PostgreSQL database dump complete
--


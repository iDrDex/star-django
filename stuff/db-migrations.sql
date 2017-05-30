--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_migrations (id, app, name, applied) FROM stdin;
7	tags	0001_initial	2015-03-13 14:22:07.017813+07
8	tags	0002_load_validations	2015-03-13 14:22:07.082146+07
9	tags	0003_cascade_behavior_on_series_tag_delete	2015-03-13 14:22:07.173563+07
10	tags	0004_validation_stats	2015-04-30 22:21:59.996201+07
11	tags	0005_userstats	2015-04-30 22:22:00.058113+07
12	tags	0006_payments	2015-05-14 19:55:13.873936+07
13	tags	0007_payment_state_and_extra	2015-06-29 12:10:52.021722+07
14	tags	0008_validations_crosscheck	2015-07-24 18:43:58.587894+07
15	tags	0009_complex_earnings	2015-07-27 18:02:01.623265+07
16	tags	0010_fill_earnings	2015-07-27 18:02:01.710829+07
17	tags	0011_remove_userstats_samples_payed	2015-07-27 18:02:01.810285+07
18	tags	0012_on_demand_validations	2015-07-30 17:32:18.693125+07
19	tags	0013_canonical_annotations	2015-08-10 18:38:43.648007+07
20	tags	0014_serieannotation_samples	2015-09-22 18:36:57.180373+07
21	tags	0015_fill_sample_counts_in_serie_annos	2015-09-22 18:36:57.448417+07
22	contenttypes	0001_initial	2015-10-14 15:31:42.979041+07
23	contenttypes	0002_remove_content_type_name	2015-10-14 15:31:43.0271+07
24	legacy	0001_initial	2015-10-14 15:32:06.365035+07
25	auth	0001_initial	2015-10-14 15:32:16.659864+07
26	admin	0001_initial	2015-10-14 15:32:38.240505+07
27	auth	0002_django_18_changes	2015-10-14 15:48:05.822104+07
28	legacy	0002_rebind_user_fks	2015-10-14 15:48:18.827171+07
29	tags	0016_rebind_user_fks	2015-10-14 15:48:19.311038+07
31	sessions	0001_initial	2015-10-14 16:13:29.972633+07
32	tags	0017_serievalidation_ignored	2015-10-20 16:00:16.268446+07
33	legacy	0003_analysis_df	2015-11-03 16:06:14.651314+07
34	legacy	0004_analysis_fold_changes	2015-11-11 17:49:30.893089+07
35	legacy	0005_analysis_success	2015-11-11 17:49:31.106577+07
36	legacy	0006_fill_analysis_success	2015-11-11 17:49:31.889604+07
37	legacy	0007_fix_char_bools	2016-02-29 12:01:42.331055+07
38	legacy	0008_allow_nonunique_deleted_tags	2016-02-29 12:01:42.468087+07
39	legacy	0009_drop_legacy_user_prepare_to_move_tag_tables	2016-03-02 15:32:25.589294+07
40	tags	0018_move_tag_tables_in	2016-03-02 15:32:26.16208+07
41	legacy	0010_move_tag_tables_out	2016-03-02 15:32:26.173605+07
42	auth	0003_remove_webpy_tables	2016-05-16 17:03:40.017283+07
43	auth	0004_rename_auth_tables_back	2016-05-16 17:03:40.07089+07
44	core	0001_initial	2016-05-16 17:03:40.080921+07
45	core	0002_user_competent	2016-05-16 17:16:14.429881+07
46	tags	0019_serievalidation_by_incompetent	2016-05-23 19:27:22.967092+07
47	tags	0020_serieannotation_captive	2016-06-09 18:40:25.143422+07
48	legacy	0011_store_attrs_in_json	2016-07-19 17:48:45.16201+07
49	legacy	0012_series_fts	2016-07-19 17:48:45.216971+07
50	tags	0021_ontologies	2016-09-12 18:35:37.064304+07
51	legacy	0013_silent_blank_change	2016-09-29 20:37:00.41703+07
52	legacy	0014_remove_attr_tables_and_views	2016-09-29 20:37:02.746911+07
53	legacy	0015_add_platform_specie	2016-10-31 20:54:04.90424+07
54	legacy	0016_platform_stats	2016-11-17 19:42:12.238314+07
55	legacy	0017_platform_verdict	2016-11-21 21:14:28.741371+07
56	legacy	0018_fill_platform_verdict	2016-11-21 21:14:33.241827+07
57	legacy	0019_update_platform_fields	2016-11-21 21:14:33.656035+07
58	legacy	0020_fix_fts	2016-11-21 21:14:56.352907+07
59	legacy	0021_nulls_and_indexes	2016-12-02 17:31:54.98188+07
60	legacy	0022_make_indexes	2016-12-02 17:32:00.571858+07
61	legacy	0023_series_specie	2016-12-07 12:07:42.454325+07
62	core	0003_statisticcache	2016-12-07 12:53:08.527664+07
63	legacy	0024_analysis_specie	2016-12-07 13:25:54.532322+07
64	legacy	0024_series_platforms	2016-12-07 19:18:05.314333+07
65	legacy	0025_merge	2016-12-07 19:18:05.322064+07
66	legacy	0026_auto_20161207_1257	2016-12-07 20:02:50.567967+07
67	authtoken	0001_initial	2017-03-03 16:34:39.194671+07
68	authtoken	0002_auto_20160226_1747	2017-03-03 16:34:39.287245+07
69	core	0004_create_users_tokens	2017-03-03 16:34:39.734767+07
70	tags	0022_add_note_and_from_api	2017-03-03 16:34:40.242448+07
72	tags	0023_fix_tags_models	2017-04-21 16:11:38.698347+07
76	tags	0024_snapshot	2017-05-01 13:20:13.411881+07
\.


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('django_migrations_id_seq', 76, true);


--
-- PostgreSQL database dump complete
--


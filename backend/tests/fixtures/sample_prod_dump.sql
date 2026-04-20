-- Fixture Story 10.7 AC5 — dump PROD synthétique avec 10+ PII FR/AO enfouis
-- Tous les identifiants/noms/emails/phones sont FICTIFS mais conformes aux
-- formats réels (RCCM OHADA, NINEA SN, IFU CI, téléphones CEDEAO, etc.).
-- Utilisé par tests/test_scripts/test_anonymize_prod_to_staging.py (E2E).

-- PostgreSQL database dump (extrait synthétique)

SET statement_timeout = 0;
SET client_encoding = 'UTF8';

--
-- Data for Name: companies
--

COPY public.companies (id, name, legal_rep, rccm, ninea, ifu, contact_email, contact_phone, address, founded_date) FROM stdin;
1	Ferme Agro Sahel	El Hadj Moussa Diop	RCCM SN DKR 2020-B-12345	123456789 A 1	1234567890A	contact@agro-sahel.sn	+221 77 123 45 67	123 rue des Baobabs Dakar	2020-03-15
2	Cooperative Riziere	Mme Aminata Sow	RCCM CI ABJ 2019-A-98765	987654321 B 2	IFU 9876543210	info@cooperative-ci.ci	+225 07 11 22 33 44	45 avenue de la Paix Abidjan	2019-06-22
3	Transports Verts	M. Ibrahim Traore	RCCM BF OUA 2021-C-55555	555555555 C 3	IFU 5551234567	direction@transports-verts.bf	+226 70 11 22 33	78 boulevard Nelson Mandela Ouagadougou	2021-01-10
\.

--
-- Data for Name: users
--

COPY public.users (id, email, full_name, birth_date, cni, bank_iban, last_login_ip) FROM stdin;
10	seydou.ndiaye@client.sn	Seydou Ndiaye	1985-04-12	1 234 5678 91234	SN08 SN01 0123 4567 8912 3456	192.168.12.34
11	fatou.sall@mefali.example.com	Fatou Sall	1990-11-23	2 567 8901 23456	SN12 SN02 9876 5432 1098 7654	10.0.45.67
12	admin@anonymized.test	Agent Ops	1975-01-01	\N	\N	127.0.0.1
\.

--
-- Data for Name: company_profiles
--

COPY public.company_profiles (id, company_id, bio, financial_records) FROM stdin;
100	1	Entreprise fondee par El Hadj Moussa Diop en 2020, specialisee dans l'agriculture biologique au Senegal. Chiffre d'affaires 2023 : 125 000 000 F CFA. Contact privilegie: Dr Cheikh Fall (cheikh.fall@agro-sahel.sn).	Revenus 2023: 125 000 000 FCFA. Investissement initial: 45 000 000 XOF.
101	2	Cooperative de producteurs de riz dirigee par Mme Aminata Sow. Adresse postale : 45 avenue de la Paix Abidjan. Numero NIF ML 98765432B.	Capital social: 30 000 000 XOF. BIC: CBAOSNDAXXX.
\.

-- End of synthetic dump

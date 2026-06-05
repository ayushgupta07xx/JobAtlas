# JobAtlas — PESTLE Analysis

External macro-environmental factors affecting the Indian online-recruitment market and JobAtlas's position within it.

## Political
- Government digital-employment initiatives (Skill India, Digital India) expand the online job-seeking base and normalise digital hiring.
- Evolving labour codes and gig/platform-worker regulation shape how platforms operate and classify work.
- Policy direction on data localisation and platform accountability influences where and how user data may be stored and processed.

## Economic
- The Indian online-recruitment market is sized at approximately **₹8,400 cr, growing ~22% YoY**, indicating sustained demand.
- Tech hiring is cyclical; IT-services and global-capability-centre (GCC) hiring in India drives much of the volume and is sensitive to global conditions.
- A structural mismatch — fresher oversupply versus senior-talent scarcity — underpins the differentiated value of the three target segments.

## Social
- A large, young, mobile-first workforce with rising graduate output, increasingly from tier-2/3 cities.
- Growing comfort with online and remote job search, and rising expectations of salary transparency.
- A trust deficit with recruiter spam and opaque processes creates demand for signal over noise.

## Technological
- Embeddings and open-source language models make semantic matching feasible at low cost (e.g. pgvector + sentence-transformers).
- Cheap mobile data and high smartphone penetration make mobile-first delivery essential.
- ATS fragmentation in India (Keka, Darwinbox, Zoho dominate over Greenhouse/Lever/Ashby) shapes which original-posting feeds are accessible.

## Legal
- Source terms of service and robots.txt govern permissible ingestion; the product uses official APIs and avoids commercial redistribution and bot-wall defeat.
- The Digital Personal Data Protection (DPDP) Act, 2023 governs handling of personal data such as resumes, reinforcing transient processing and minimal retention.
- Intellectual-property and database-rights considerations apply to aggregated content and inform the no-redistribution stance.

## Environmental
- As a digital product the direct footprint is small; the free-tier/serverless posture keeps idle compute low.
- Cloud-warehouse usage is demonstration-only and torn down after use, minimising sustained energy consumption.

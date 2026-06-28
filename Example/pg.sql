INSERT INTO holder (did, display_name, email) VALUES
('did:example:123', 'Alice', 'alice@example.com');

INSERT INTO issuer (did, display_name, endpoint, public_key_jwk) VALUES
('did:example:issuer', 'Example University', 'https://example.edu/issuer', '{"kty":"OKP","crv":"Ed25519","x":"..."}');

INSERT INTO credential (
    holder_id, issuer_id, vc_id, type, context, schema_uri, issuance_date, tags,
    credential_subject, proof, raw_vc
) VALUES (
    1, 1, 'urn:uuid:abc123',
    '["VerifiableCredential","UniversityDegreeCredential"]',
    '["https://www.w3.org/2018/credentials/v1"]',
    'https://example.edu/schemas/degree.json',
    '2026-06-28T12:00:00Z',
    '["education","degree","computer-science"]',
    '{"id":"did:example:123","degree":{"type":"BachelorDegree","name":"B.Sc. Computer Science"}}',
    '{"type":"Ed25519Signature2018","created":"2026-06-28T12:00:00Z","proofPurpose":"assertionMethod","verificationMethod":"did:example:issuer#keys-1","jws":"..."}',
    '{"@context":["https://www.w3.org/2018/credentials/v1"],"id":"urn:uuid:abc123",...}'
);

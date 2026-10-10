# Operação do site

Este repositório publica `felipedelgadopsicologo.com.br` diretamente da raiz da branch `master` pelo GitHub Pages.

## Regras

- Não invente nem altere CRP, formação, especialidades, preço, modalidade, local de atendimento ou alegações clínicas sem validação do responsável profissional.
- Não adicione formulários, analytics ou terceiros que coletem dados sem destino, finalidade, consentimento e política confirmados.
- Nunca versione segredo, token, senha, `.env` ou dado de paciente.
- Toda mudança deve preservar canonical, sitemap, robots, `llms.txt`, acessibilidade e links internos.
- Rode `python -m unittest discover -s tests -v` antes de commit.
- Push em `master` publica em produção e exige autorização explícita, rollback conhecido e smoke test.

## Rollback

Reverta por novo commit; não reescreva o histórico publicado. O baseline anterior ao onboarding do Tesseract é `65258c04664ba8fff82e37bef0cad5ab564a0cc0`.

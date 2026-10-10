# felipedelgadopsicologo.com.br

Site institucional estático de Felipe Delgado, publicado pelo GitHub Pages a partir da raiz da branch `master`.

## Estrutura

- `index.html`: página inicial;
- diretórios de serviço: páginas internas;
- `assets/`: CSS, JavaScript e imagens;
- `robots.txt`, `sitemap.xml` e `llms.txt`: descoberta;
- `404.html`: página de erro não indexável;
- `tests/`: validações locais e de CI.

Não há build nem backend. O contato inicial usa links diretos para o WhatsApp; o site não deve ganhar formulário ou coleta de dados sem infraestrutura e revisão de privacidade confirmadas.

## Validação

```powershell
python -m unittest discover -s tests -v
```

## Publicação e rollback

Push em `master` aciona o GitHub Pages. Antes de publicar, registre o HEAD em produção e obtenha autorização explícita. Depois, confirme home, páginas internas, `robots.txt`, `sitemap.xml`, `llms.txt` e uma URL inexistente. Rollback é feito por novo commit de reversão, sem reescrever o histórico.

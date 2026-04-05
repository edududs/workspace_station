# workspace

CLI para gerenciar repositórios clonados dentro de `projects/`, com arquitetura hexagonal.
Os outputs do terminal usam `Rich` para tabelas, painéis e mensagens de erro mais legíveis.
O diretório raiz `workspace/` é o home operacional da ferramenta: catálogo, segredos, configs e paths exibidos partem dele.

## Estrutura

- `src/workspace/application`: portas e casos de uso.
- `src/workspace/domain`: modelos de domínio.
- `src/workspace/adapters`: CLI, Git, catálogo JSON, segredos e filesystem.
- `src/workspace/bootstrap`: composição da aplicação.

## Segredos

Guarde a chave privada em `.secrets/id_workspace`.
O CLI usa apenas o caminho do arquivo para clones SSH e não imprime o conteúdo da chave.

## Comandos

```bash
uv run wrkspc list
uv run wrkspc clone whatsapp_bot
uv run wrkspc clone git@github.com:org/new-service.git
uv run wrkspc clone https://github.com/org/new-service.git --force
uv run wrkspc delete whatsapp_bot --force
```

## Catálogo

Os aliases ficam em `projects.json`. Quando você clona por URL, o alias inferido passa a ser persistido lá.

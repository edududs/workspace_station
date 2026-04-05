# workspace

CLI para gerenciar repositórios clonados dentro de `projects/`, com arquitetura hexagonal.
Os outputs do terminal usam `Rich` para tabelas, painéis e mensagens de erro mais legíveis.
O diretório raiz `workspace/` é o home operacional da ferramenta: catálogo, segredos, configs e paths exibidos partem dele.
O `workspace` também é um `uv workspace`, com membros Python explícitos em `tool.uv.workspace.members`.

## Estrutura

- `src/workspace/application`: portas e casos de uso.
- `src/workspace/domain`: modelos de domínio.
- `src/workspace/adapters`: CLI, Git, catálogo JSON, segredos e filesystem.
- `src/workspace/bootstrap`: composição da aplicação.

## Git

O adapter padrão usa `dulwich`.
Também existe um adapter alternativo baseado no binário local `git`, mantido no código mas fora do wiring padrão.

## Python

A versão recomendada e pinada na raiz é `3.13` via `.python-version`.
Para um projeto em `projects/*` participar bem do workspace, ele precisa aceitar Python `3.13` em `project.requires-python`.
Se algum membro não aceitar `3.13`, o `uv` tende a falhar no `lock` ou `sync` do workspace, o que funciona como a validação natural dessa regra.
Um glob amplo como `projects/*` não é seguro no `uv`, porque qualquer diretório sem `pyproject.toml` quebra a descoberta do workspace.

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
uv run wrkspc sync
uv run check
uv run check src/workspace tests
uv run check -I tests
uv run check . -I tests -I projects/legacy
uv run cache_clean
uv run cache_clean src/workspace projects/whatsapp_bot
```

## Catálogo

Os aliases ficam em `projects.json`. Quando você clona por URL, o alias inferido passa a ser persistido lá.
Quando um projeto em `projects/` tem `pyproject.toml`, o `wrkspc` também sincroniza automaticamente
o bloco `[tool.uv.workspace].members` na raiz.

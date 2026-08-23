---
name: ask
description: "Responde perguntas em linguagem natural sobre como um produto funciona por dentro, indo até o código-fonte real para responder — sem exigir que quem pergunta saiba nada de grafos, subdomínios, repositórios ou scripts. Funciona em qualquer repositório que correlacione domínio e código (um context-repo: CONTEXT-MAP.md + CONTEXT.md com `realizado_por`), traduzindo sozinha a pergunta de negócio para o contexto certo, o componente certo e o caminho certo dentro dele, e então lendo o código via /graphify. Use sempre que alguém perguntar 'como funciona X no produto?', 'onde o sistema faz Y?', 'o que acontece quando Z?', 'isso já está implementado?', 'me mostra como isso funciona de verdade' — mesmo sem citar 'grafo', 'graphify', 'subdomínio' ou 'componente'. Serve tanto PM querendo confirmar comportamento quanto pessoa técnica querendo ir além do que a documentação diz. É estritamente leitura: nunca edita CONTEXT.md, doc de componente ou qualquer arquivo de domínio — quando encontra uma lacuna no modelo, repassa para quem é dono da escrita."
metadata:
  language: agnostic
  tags: [ddd, domain, graphify, context-repo, onboarding, discovery]
---

# ask

Ponte entre uma pergunta de negócio e a resposta que vem do código, sem que quem
pergunta precise saber que por trás disso existem contextos, componentes técnicos,
grafos temporários e a skill `/graphify`.

**Regra de ouro:** quem pergunta só pensa em produto. Toda decisão técnica (qual
componente, qual caminho, se precisa baixar código) é sua responsabilidade resolver
sozinho — só volte ao usuário quando a ambiguidade for de **produto** (ex.: "isso é
sobre o app mobile ou o painel web?"), nunca de implementação (nunca pergunte "quer que
eu use o caminho `src/checkout`?").

**Esta skill nunca escreve.** Ela lê o modelo, lê o código e responde. Quando encontra
uma lacuna, repassa para quem é dono da escrita — ver "Quando falta alguma coisa".

## Passo 0 — Dependências

Você precisa de duas coisas instaladas no repositório-alvo:

- **`blueprintfy`** — dela vêm `scripts/graph_query.py` (o grafo do modelo) e
  `scripts/repo_cache.py` (resolver código de componente). Procure em
  `.claude/skills/blueprintfy/` e `.agents/skills/blueprintfy/`.
- **`graphify`** — para ler o código de fato.

A pasta onde este próprio `ask` está instalado (`.claude/skills` ou `.agents/skills`)
já diz qual é a plataforma agêntica em uso — não pergunte isso.

Se o `blueprintfy` faltar: confirme com o usuário e rode, da raiz do repositório-alvo,
`scripts/install-blueprintfy.sh <owner/repo-do-catalogo> <pasta-de-skills-detectada>`
(o script acompanha esta skill; default do catálogo: `luishpcosta/ai-lup-skills`).
Ele clona raso e temporário via `gh`, copia só a skill e remove o clone. Exige `gh`
autenticado (`gh auth status`) — se não estiver, explique e ofereça `gh auth login`
em vez de travar em silêncio.

## Passo 1 — Confirme que isto é um context-repo

```bash
test -f CONTEXT-MAP.md && echo sim
```

`CONTEXT-MAP.md` na raiz é o marcador. Sem ele, não há correlação domínio↔código para
consultar: diga isso ao usuário e ofereça o `context-repo-bootstrap`, que cria essa
estrutura. Não tente adivinhar a arquitetura lendo o repositório na mão.

Rode tudo com o diretório de trabalho na raiz desse repositório.

## Passo 2 — Ache o contexto certo

Os contextos estão na seção `## Contextos` do `CONTEXT-MAP.md`, cada um com uma
descrição curta e um `CONTEXT.md` com o glossário completo.

Compare a pergunta com o **significado** de cada contexto, não com palavras-chave
soltas. Uma pergunta como "como a luz acende quando eu chego em casa" costuma cruzar
dois contextos (o que dispara e o que é disparado) — abra o glossário dos candidatos e
veja qual casa com os termos exatos da pergunta.

Só pergunte ao usuário se depois disso ainda estiver genuinamente ambíguo, e pergunte
em linguagem de produto, nunca citando slugs.

Se o contexto escolhido tiver subcontextos (`dominio_pai`), não se preocupe: o Passo 3
desce a hierarquia sozinho.

## Passo 3 — Descubra que código realiza esse contexto

```bash
python3 <pasta-de-skills>/blueprintfy/scripts/graph_query.py realiza "<Nome do Contexto>"
```

Isso devolve, para o contexto e todos os seus subcontextos: os componentes, os
**caminhos declarados dentro de cada um**, e as revisões (`local`, `remote`, `ref`,
pin). Não há heurística aqui — o caminho é dado declarado no modelo. Se ele estiver
errado, isso é uma lacuna do modelo, não um chute seu para corrigir (ver "Quando falta
alguma coisa").

Quando um componente vier sem caminho, vale o repositório inteiro — é o normal para
componentes pequenos.

Se a saída trouxer **⚠ DESCASADO**, o código andou desde o commit que a documentação
descreve. Isso não impede a resposta, mas muda o que você diz no final: avise, em uma
frase e sem jargão de git, que a documentação foi escrita olhando uma versão anterior.

Se o contexto for realizado por mais de um componente, tente decidir sozinho pelo teor
da pergunta ("o app do celular trava quando…" aponta para o app, não para o painel
web). Só pergunte quando a pergunta realmente não indicar — e em linguagem de produto.

## Passo 4 — Resolva o código para um diretório no disco

O `realiza` devolve o que está declarado; quem transforma isso em um diretório é o
`repo_cache`:

```python
import sys; sys.path.insert(0, "<pasta-de-skills>/blueprintfy/scripts")
import repo_cache
res = repo_cache.resolve("<componente>", <front matter do doc de componente>,
                         "<raiz do repo>", rev="latest")
```

Use **`rev="latest"`** (o `ultimo_visto`): a pergunta é sobre como o produto funciona
hoje. `rev="pin"` é para quando a pergunta cita um documento ("o PRD dizia que…") e
você precisa do código que aquele documento descrevia.

O clone local vence e não baixa nada. Se não existir nesta máquina, o `repo_cache`
baixa para `.repo-cache/<componente>/` na primeira vez e reaproveita depois — repasse
isso ao usuário em linguagem simples ("primeira pergunta sobre essa parte, precisei
baixar o código; só acontece uma vez"), nunca como jargão de git.

## Passo 5 — Leia o código com `/graphify`

Cheque primeiro se o grafo já existe:

```bash
ls .graphs/<contexto>/<componente>/graphify-out/graph.json 2>/dev/null
```

Se existir, **não reconstrua** — pule direto para a query. Só reconstrua se o usuário
pedir atualização explicitamente, ou se a pergunta exigir código que você sabe não
estar coberto.

Se não existir: crie `.graphs/<contexto>/<componente>/`, entre nela, e invoque
`/graphify` apontando para o **caminho absoluto** resolvido no Passo 4 (concatenado com
o caminho declarado, quando houver). O diretório de trabalho dentro de `.graphs/…` é o
que garante que o `graphify-out/` nasce no context-repo e não no repositório da
aplicação.

Quando houver vários caminhos declarados para o mesmo componente, grafique-os no mesmo
diretório de grafo — eles são partes de um mesmo contexto.

Depois, invoque `/graphify` em modo query com a pergunta original. Você pode reformular
ancorando em termos do glossário para achar os nós certos, mas não troque o sentido da
pergunta.

Para atualizar um grafo existente, entre na pasta dele e rode o mesmo `/graphify` com
`--update`: reprocessa só o que mudou, em vez de reconstruir tudo.

## Passo 6 — Responda em linguagem de produto

A saída do `graphify query` vem em termos de grafo (nós, arestas, comunidades,
`source_location`). Antes de repassar:

- Reescreva como se estivesse explicando o comportamento do produto para alguém que
  nunca leu o código.
- Cite arquivo e linha como **referência para conferir**, não como o corpo da resposta.
- Não mencione "nó", "aresta", "comunidade", "grafo" ou nomes de script, a menos que o
  usuário pergunte como você chegou lá.
- Se a resposta ficou incompleta porque o caminho declarado cortou referências que
  vivem fora dele, diga isso em uma frase e ofereça rodar de novo sem escopo.

**A resposta não vira documento.** Por padrão ela é leitura e apresentação: nada é
gravado em lugar nenhum. Se o usuário quiser materializá-la (virar seção de PRD, SPEC,
ADR), aí sim repasse para a skill dona daquele documento — nunca escreva você mesmo.

## Quando falta alguma coisa — repasse, não escreva

Três lacunas diferentes, três donos diferentes. Em todas: descreva o que achou,
proponha o encaminhamento, e siga só com confirmação.

| O que falta | Sintoma | Dono |
|---|---|---|
| Linguagem de domínio | A pergunta usa um termo que nenhum glossário tem, ou o código revelou um conceito que o modelo não nomeia | `blueprintfy` |
| Componente ou caminho | `realiza` não devolve nada, ou o caminho declarado não existe mais no código | `context-repo-bootstrap` |
| Nada — só a resposta | O modelo cobre a pergunta | ninguém: responda e pare |

O caso mais comum e mais valioso é o primeiro: a pessoa pergunta sobre algo real do
produto que o modelo de domínio ainda não descreve. Não invente o termo e não grave
nada — traga a descoberta ("o código faz X, e isso não tem nome no glossário deste
contexto") e ofereça chamar o `blueprintfy` para nomeá-la direito.

## Limpeza

`.graphs/` e `.repo-cache/` são git-ignorados e descartáveis. Ao final, se fizer
sentido, ofereça apagar — mas só execute com confirmação explícita, mesmo sendo lixo:
é uma remoção, trate como tal. Se o usuário for fazer mais perguntas na sequência,
sugira manter.

## Erros comuns a evitar

- Perguntar ao usuário algo técnico (nome de script, caminho, "qual componente") em
  vez de resolver sozinho ou traduzir para uma pergunta de produto.
- Adivinhar o caminho dentro do componente com `find`/`du`. O caminho é dado declarado;
  se está errado ou faltando, isso é lacuna do modelo, não convite para heurística.
- Parar depois do `realiza`, achando que o trabalho acabou — ele só diz onde olhar.
- Editar `CONTEXT.md`, doc de componente ou `CONTEXT-MAP.md` para "ajudar" a resposta.
  Este fluxo é estritamente leitura.
- Versionar `.graphs/` ou `.repo-cache/`.

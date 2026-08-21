---
name: ask
description: >
  Responde perguntas em linguagem natural sobre como o produto (a POC Home
  Assistant) funciona por dentro, sem exigir que quem pergunta saiba nada de
  grafos, /graphify, subdomínios ou os scripts do context-repo. Use sempre que
  o usuário fizer uma pergunta do tipo "como funciona X no app/produto?",
  "onde/como o sistema faz Y?", "o que acontece quando Z acontece?", mesmo
  sem citar termos técnicos como "grafo", "graphify" ou "subdomínio" — a skill
  traduz a pergunta de negócio para o fluxo técnico sozinha. Dispara com
  `/ask <pergunta>` ou com frases soltas como "pergunta sobre o domínio",
  "como funciona X no produto", "quero entender como Y é implementado".
  Não é para editar catalog-info.yaml, CONTEXT.md ou qualquer arquivo de
  domínio — é só leitura sobre o catálogo já existente.
metadata:
  language: agnostic
  tags: [ddd, domain, graphify, catalog, onboarding]
---

# ask

Ponte entre uma pergunta de negócio ("como uma automação reage a um evento?")
e a resposta que vem direto do código, sem que quem pergunta precise saber
que por trás disso existem subdomínios, componentes técnicos, grafos
temporários e a skill `/graphify`. Todo esse mecanismo é descrito em
`docs/como-perguntar-por-subdominio.md` — leia esse arquivo se precisar de
detalhes do "porquê" por trás de qualquer passo abaixo.

**Regra de ouro:** a pessoa que pergunta só pensa em produto. Toda decisão
técnica (qual componente, qual pasta, se precisa de `--path`) é sua
responsabilidade resolver sozinho, olhando os dados disponíveis — só volte
para o usuário quando a ambiguidade é sobre **produto** (ex.: "isso é sobre o
app mobile ou o painel web?"), nunca sobre implementação (ex.: nunca pergunte
"quer que eu rode com `--path homeassistant/components/automation`?").

## Pré-condição

Rode tudo com o diretório de trabalho dentro de `context-repo/`. Se não
estiver lá, `cd` primeiro. Você não precisa (e não deve) editar
`catalog-info.yaml` ou qualquer `CONTEXT.md` neste fluxo — é consumo
read-only do catálogo já publicado.

## Passo 1 — Entenda a pergunta e ache o subdomínio certo

Rode:

```bash
python3 scripts/query_catalog.py list-domains
```

Isso lista os 5 subdomínios de produto com descrição curta e uma amostra do
glossário. Compare a pergunta do usuário com o **significado** de cada
subdomínio, não com palavras-chave soltas — "como uma luz liga quando eu
chego em casa" é `automation-state-engine` (Trigger/Action) cruzando com
`integration-platform` (a luz em si é uma Entity de uma Integration), por
exemplo.

Se a pergunta claramente aponta para um único subdomínio, prossiga direto.
Se ficou em dúvida entre dois (ex.: a pergunta toca tanto "automação" quanto
"dispositivo conectado"), rode:

```bash
python3 scripts/query_catalog.py domain <slug-candidato>
```

para os candidatos e olhe o glossário completo — geralmente um dos dois casa
melhor com os termos exatos da pergunta. Só pergunte ao usuário se depois
disso ainda estiver genuinamente ambíguo, e pergunte em termos de produto,
não de subdomínio (ex.: "essa pergunta é mais sobre a automação em si
disparando, ou sobre o dispositivo que ela controla?" — nunca "é
automation-state-engine ou integration-platform?").

## Passo 2 — Resolva o componente técnico

Alguns subdomínios têm mais de um componente técnico realizador:

- `addon-system-management` → `supervisor` **ou** `operating-system`
- `client-experience` → `frontend` (web) **ou** `android` **ou** `ios`

Se o subdomínio escolhido tem só um componente (`automation-state-engine`,
`integration-platform` → sempre `core`; `build-distribution` → sempre
`docker`), siga sem perguntar nada.

Se tem mais de um, primeiro tente decidir sozinho pelo teor da pergunta (ex.:
"o app do celular trava quando..." → claramente `android`/`ios`, não
`frontend`). Só pergunte ao usuário quando a pergunta realmente não indica
qual — e pergunte em linguagem de produto: "isso é sobre o app mobile, o
painel web, ou os dois?" / "isso é sobre os add-ons em si, ou sobre o sistema
operacional por baixo (Home Assistant OS)?". Nunca diga "componente" ou
"repositório" para o usuário.

## Passo 3 — Gere os comandos com `ask`

Antes de rodar `ask`, cheque se já existe um grafo para esse par
subdomínio/componente:

```bash
ls .graphs/<slug>/<componente>/graphify-out/graph.json 2>/dev/null
```

Se existir, você **não precisa reconstruir nada** — pule direto para o Passo
5 e rode só a query (`graphify query "..."`) em cima do grafo existente. Só
reconstrua (Passo 5 completo, ou `--update`, ver Passo 7) se o usuário
pedir uma atualização explicitamente ou se a pergunta exigir código que você
sabe não estar coberto pelo grafo atual.

Se não existir, rode:

```bash
python3 scripts/query_catalog.py ask <slug-do-dominio> "<pergunta original do usuário>" [componente]
```

Isso cria (de verdade, no disco) a pasta `.graphs/<slug>/<componente>/` e
imprime os 3 comandos prontos (`cd`, `/graphify <caminho>`, `/graphify query
"..."`). Você vai executá-los você mesmo nos próximos passos — não é
necessário copiar/colar manualmente, você já tem os caminhos na saída.

O `<caminho>` impresso é o `repository.local` do componente (guardado no
catálogo relativo à raiz do repo, ex.: `../core`) já resolvido para absoluto —
é o absoluto que você usa, porque o `/graphify` roda de dentro de
`.graphs/<slug>/<componente>/`, onde um caminho relativo apontaria pro lugar
errado. Se essa pasta não existir nesta máquina (ex.: você só tem o
`context-repo` clonado, sem os repos-fonte), o próprio `ask` percebe e cai
para `repository.remote`
automaticamente — clona o repo pinado no commit documentado no catalog para
`.repo-cache/<componente>/` (só na primeira vez; reaproveita depois) e usa
esse caminho no lugar. Você vai ver linhas começando com `>` avisando disso —
repasse esse aviso ao usuário de forma simples (algo como "primeira pergunta
sobre isso, precisei baixar o código — só acontece uma vez") em vez de
ignorar ou entrar em jargão de git. Use sempre o caminho que o comando
efetivamente imprimiu nos passos seguintes, nunca assuma o caminho local
fixo.

## Passo 4 — Decida se precisa escopar com `--path`

Alguns componentes são grandes demais para escanear inteiros com qualidade
(o `core`, por exemplo, tem 600MB+). Antes de rodar o `/graphify`, cheque o
tamanho do componente usando o caminho que o Passo 3 imprimiu:

```bash
du -sh <caminho-impresso-pelo-passo-3>
```

Se for grande (na prática, hoje só `core` está nessa faixa — os demais
componentes são pequenos o suficiente para escanear inteiros sem problema),
não pergunte ao usuário nada sobre pastas — **você** localiza a subpasta
certa olhando a estrutura real do repositório e os termos de glossário da
pergunta:

```bash
find <caminho-impresso-pelo-passo-3> -maxdepth 3 -type d -iname "*<termo-do-glossario>*"
```

`docs/como-perguntar-por-subdominio.md` mostra um exemplo real: para uma
pergunta sobre `automation-state-engine` no `core`, a pasta certa é
`homeassistant/components/automation`. Use esse tipo de raciocínio — procure
pelo nome do domínio/subdomínio ou de um termo de glossário central dentro de
`homeassistant/components/` (ou equivalente no componente em questão). Se
achar uma pasta clara, refaça o comando do Passo 3 com `--path <subpasta>`.
Se não achar nada óbvio, sem problema: rode sem `--path` (repositório
inteiro) — é mais lento, não é errado.

**Aviso a levar em conta, não a repassar em jargão:** escopar com `--path`
pode deixar algumas referências "soltas" (código que aponta para fora da
pasta escaneada). Isso é normal e não invalida a resposta; se a resposta
final parecer incompleta por depender de algo fora do escopo, rode de novo
sem `--path` (repo inteiro) antes de desistir.

## Passo 5 — Rode os comandos de verdade

Na ordem impressa pelo Passo 3 (ajustando o `--path` se você decidiu usar
um no Passo 4):

1. Confirme/crie a pasta `.graphs/<slug>/<componente>/` (o Passo 3 já criou).
2. Invoque a skill `graphify` já instalada apontando para o caminho do
   componente (ou subpasta), com o diretório de trabalho dentro da pasta
   temporária — é isso que garante que `graphify-out/` nasce em
   `.graphs/...` e não no repositório da aplicação.
3. Depois que o grafo estiver construído, invoque `graphify` de novo em modo
   de pergunta (`query`), passando a pergunta original do usuário — pode
   levemente reformular ancorando em termos do glossário se isso ajudar a
   achar os nós certos, mas não troque o sentido da pergunta.

## Passo 6 — Traduza a resposta para linguagem de produto

A resposta do `graphify query` vem em termos de grafo (nós, arestas,
comunidades, `source_location`). Antes de repassar ao usuário:

- Reescreva em português simples, como se estivesse explicando o
  comportamento do produto para alguém que nunca leu o código.
- Cite arquivo e linha (`source_location`) como referência para quem quiser
  conferir, mas não como o corpo principal da resposta.
- Não mencione "nó", "aresta", "comunidade", "grafo temporário" ou nomes de
  scripts a menos que o usuário pergunte especificamente como voce chegou
  na resposta.
- Se a resposta ficou incompleta por causa do escopo (`--path` cortando
  referências — ver Passo 4), diga isso em uma frase e ofereça rodar de novo
  sem escopo, em vez de simplesmente entregar uma resposta capenga.

## Passo 7 — Atualizando um grafo existente

Cada pasta `.graphs/<slug>/<componente>/graphify-out/` guarda um
`manifest.json` com o "fingerprint" (mtime + hash) de cada arquivo escaneado
— é isso que permite atualização incremental em vez de reconstruir tudo do
zero.

Quando o usuário pedir para atualizar (ex.: "o código mudou, refaz essa
análise", "atualiza o grafo de X"), **não** apague a pasta e recrie: entre
nela e rode o mesmo comando `/graphify <mesmo caminho usado antes>`, mas com
`--update`:

```bash
cd .graphs/<slug>/<componente>
/graphify <mesmo caminho de antes> --update
```

Isso reprocessa só o que mudou (arquivo novo, editado ou removido) e
reaproveita o resto do grafo — muito mais rápido que o build completo.
Depois de atualizar, rode a query de novo normalmente (Passo 5/6).

Se o usuário só quer perguntar algo novo sobre o **mesmo** código já
mapeado (nada mudou no repositório), não atualize nada — vá direto para a
query (ver a checagem no Passo 3).

Só descarte e recrie do zero (`rm -rf .graphs/<slug>/<componente>/` seguido
de um novo `ask`) se o `--update` não bastar — por exemplo, se você decidiu
trocar o `--path` para uma pasta diferente/maior.

## Passo 8 — Limpeza (opcional, sempre com confirmação)

`.graphs/` é git-ignorado e descartável. Ao final, se fizer sentido, ofereça:
"posso apagar o grafo temporário que criei para essa pergunta (`rm -rf
.graphs/`)?" — só execute com confirmação explícita do usuário, mesmo sendo
lixo descartável (é uma remoção, trate como tal). Se o usuário for fazer mais
perguntas na sequência, sugira manter — grafos já construídos não precisam
ser refeitos para a mesma pergunta/componente.

## Erros comuns a evitar

- Perguntar ao usuário algo técnico (nome de script, flag, caminho, "qual
  componente") — sempre traduza para uma pergunta de produto, ou melhor,
  resolva sozinho sem perguntar.
- Rodar `ask` e parar aí, achando que o trabalho terminou — `ask` só imprime
  os comandos, você precisa efetivamente rodar `/graphify` e a query.
- Editar `catalog-info.yaml` ou `CONTEXT.md` para "ajudar" a resposta — este
  fluxo é estritamente read-only sobre o domínio.
- Deixar grafos em `.graphs/` fora do `.gitignore` ou tentar versioná-los —
  nunca faça `git add` nessa pasta.

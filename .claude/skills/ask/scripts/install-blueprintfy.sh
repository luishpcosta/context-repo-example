#!/usr/bin/env bash
# Instala a skill blueprintfy no repositório-alvo clonando o catálogo central
# (ai-lup-skills) via gh, de forma rasa e temporária — sem depender do CLI
# `lup-skills` estar instalado/linkado na máquina de quem está rodando isso.
# Sempre remove o clone temporário ao final, sucesso ou erro.
#
# Uso (a partir da raiz do repositório-alvo):
#   install-blueprintfy.sh <owner/repo-do-catalogo> <pasta-de-skills-do-agente>
#
# Exemplo:
#   install-blueprintfy.sh luishpcosta/ai-lup-skills .claude/skills
#
# Copia skills/blueprintfy do catálogo para <pasta-de-skills-do-agente>/blueprintfy,
# recursivo e plano (mesma convenção do `lup-skills add`: sem replicar a pasta de
# categoria de origem). Não sobrescreve uma instalação já existente — se
# <pasta-de-skills-do-agente>/blueprintfy já existir, para e avisa; confirmar
# sobrescrita é decisão de quem chama este script, não dele.

set -euo pipefail

CATALOG_REPO="${1:?uso: install-blueprintfy.sh <owner/repo> <pasta-de-skills>}"
SKILLS_DIR="${2:?uso: install-blueprintfy.sh <owner/repo> <pasta-de-skills>}"

DEST_SKILL_DIR="$SKILLS_DIR/blueprintfy"

if [[ -e "$DEST_SKILL_DIR" ]]; then
  echo "Já existe algo em $DEST_SKILL_DIR — remova ou decida a sobrescrita antes de rodar este script de novo." >&2
  exit 1
fi

TMPDIR="$(mktemp -d)"
cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

gh repo clone "$CATALOG_REPO" "$TMPDIR/catalog" -- --depth 1 --filter=blob:none

if [[ ! -d "$TMPDIR/catalog/skills/blueprintfy" ]]; then
  echo "Não encontrei skills/blueprintfy em $CATALOG_REPO — o catálogo mudou de estrutura, ou o owner/repo está errado?" >&2
  exit 1
fi

mkdir -p "$SKILLS_DIR"
cp -r "$TMPDIR/catalog/skills/blueprintfy" "$DEST_SKILL_DIR"

echo "blueprintfy instalado em $DEST_SKILL_DIR"

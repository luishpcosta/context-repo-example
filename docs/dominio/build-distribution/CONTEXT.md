---
contexto: Build & Distribution
depende_de: []
---

# Build & Distribution

Subdomínio genérico de suporte: garante que os demais componentes cheguem ao usuário
final de forma consistente e executável em diferentes arquiteturas de hardware. Não
carrega diferencial de produto — é infraestrutura de entrega.

Realizado tecnicamente pelo componente `docker` (ver `../../../catalog-info.yaml`).

## Linguagem

**Base Image**:
A imagem de container fundamental (runtime + dependências de sistema) sobre a qual as
imagens distribuídas do produto (core, add-ons) são construídas.

**Container Image**:
O pacote de distribuição executável de um componente do produto, publicado em um
registro e versionado por release — é a unidade que o usuário final baixa e executa.

**Release Channel**:
A trilha de estabilidade que um usuário escolhe para receber atualizações (ex.: stable
vs. beta).

**Multi-arch Build**:
A capacidade do produto de ser distribuído para diferentes arquiteturas de hardware a
partir da mesma base de código, sem exigir que o usuário saiba qual arquitetura
escolher.

# Instruções pro Gemini CLI

As regras do editor estão no `CLAUDE.md` (o nome vem do Claude Code, mas valem igual pra você). Elas são importadas aqui:

@./CLAUDE.md

Se o conteúdo acima não apareceu, **leia o arquivo `CLAUDE.md` inteiro antes de qualquer coisa** e siga como se estivesse escrito aqui.

## Diferenças pra quem roda no Gemini CLI

- **Onde registrar:** tudo que o usuário ensinar vai no `CLAUDE.md` e em `estilos/`, como ele manda. Não escreva regras neste `GEMINI.md`: assim o projeto funciona igual com as duas IAs.
- **Comandos:** os comandos `/editar-video`, `/revisar-edicao` e `/estudar-referencia` estão em `.gemini/commands/`. Quando o `CLAUDE.md` falar em "skill" ou em `/revisar-edicao`, use esses comandos.
- **Ver as folhas de frames:** abra as imagens `.jpg` com a ferramenta de ler arquivos (ela mostra a imagem). Olhe TODAS as folhas, como o processo manda; nunca decida um corte sem ter visto o quadro.
- **Rodar as ferramentas:** use sempre o Python do projeto, `ferramentas\venv\Scripts\python.exe`, e uma tarefa pesada por vez (o PC pode ser fraco).
- **Atalho de estilo novo:** quando criar `Editor - <Nome>.bat`, copie o `ferramentas/modelo_estilo.bat` como o `CLAUDE.md` explica. Ele já abre a IA certa sozinho (Claude ou Gemini).
- **Sem chute:** se não tiver certeza do que acontece numa cena, de qual estilo usar ou do que o usuário quer, **pergunte**. É melhor perguntar do que inventar uma piada ou um corte que não faz sentido.

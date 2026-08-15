# Design System — AdventureWorks Analytics

## 1. Objetivo

Este design system orienta a criação dos protótipos no Figma e sua implementação no Power BI. O objetivo é manter uma experiência visual consistente, clara e acessível em todas as páginas do dashboard.

O sistema prioriza:

- simplicidade e leitura rápida;
- hierarquia clara entre indicadores e análises;
- aparência corporativa, moderna e leve;
- consistência entre páginas;
- reprodução viável com recursos nativos do Power BI;
- uso de cores para comunicar significado, não apenas decorar.

## 2. Direção visual

O dashboard combina:

- fundo claro e confortável para uso prolongado;
- cards brancos bem delimitados;
- navegação escura para criar contraste e orientação;
- azul como cor principal;
- roxo como apoio analítico;
- verde para resultados positivos;
- bastante espaço em branco e poucos elementos decorativos.

Palavras-chave: **clean, claro, organizado, confiável e corporativo**.

## 3. Formato e grade

### Página

| Propriedade | Valor |
| --- | ---: |
| Formato | 16:9 |
| Largura | 1280 px |
| Altura | 720 px |
| Menu lateral | 190 px |
| Área principal | 1090 px |
| Margem externa da área principal | 24 px |
| Espaço entre componentes | 16 px |

### Sistema de espaçamento

Utilizar múltiplos de 4 px:

| Token | Valor | Uso principal |
| --- | ---: | --- |
| XS | 4 px | pequenos ajustes internos |
| SM | 8 px | distância entre ícone e texto |
| MD | 12 px | padding compacto |
| LG | 16 px | espaço entre componentes |
| XL | 24 px | margens e padding de cards |
| 2XL | 32 px | separação entre seções |

## 4. Paleta de cores

### Cores estruturais

| Token | Hex | Aplicação |
| --- | --- | --- |
| Background | `#F3ECDD` | fundo geral da página |
| Surface | `#F8F3E8` | cards e áreas de conteúdo |
| Navigation | `#123E7C` | menu lateral e estrutura principal |
| Border | `#123E7C` | bordas e divisores estruturais |
| Text Primary | `#17243A` | títulos e valores principais |
| Text Secondary | `#77766F` | rótulos e informações auxiliares |
| Text On Dark | `#F8F3E8` | texto sobre o menu lateral |
| Text Muted On Dark | `#D9E3ED` | itens inativos do menu |

### Cores de dados e estados

| Token | Hex | Significado |
| --- | --- | --- |
| Primary Blue | `#123E7C` | estrutura, títulos, série principal e item ativo |
| Editorial Coral | `#F0644D` | falhas, alertas e destaques editoriais |
| Operational Green | `#247565` | sucesso operacional confirmado |
| Attention Sand | `#D59672` | atenção e ressalvas operacionais |
| Neutral Gray | `#77766F` | etapas sem monitoramento ou estado neutro |

### Regras de uso

- Manter azul, creme e coral como identidade estrutural do dashboard.
- Reservar o verde para sucesso operacional, sem usá-lo como cor estrutural.
- Usar areia e coral somente quando houver significado de atenção ou falha.
- Evitar grandes superfícies em cores saturadas.
- Não depender apenas da cor para comunicar um resultado; combinar cor com rótulo, valor, ícone ou sinal.
- Em gráficos com muitas categorias, destacar no máximo uma ou duas e manter as demais em tons neutros.

## 5. Tipografia

Fonte principal: **Segoe UI**, por sua disponibilidade e compatibilidade com o Power BI.

| Estilo | Tamanho | Peso | Uso |
| --- | ---: | --- | --- |
| Page Title | 24 px | Semibold | título da página |
| Section Title | 16 px | Semibold | títulos de cards e seções |
| KPI Value | 28 px | Semibold | valor principal dos KPIs |
| KPI Label | 12 px | Semibold | nome do indicador |
| Body | 12 px | Regular | textos e rótulos |
| Caption | 10 px | Regular | contexto, fonte e atualização |
| Navigation | 12 px | Semibold | itens do menu lateral |

Regras:

- Usar caixa alta apenas em rótulos curtos, nunca em títulos longos.
- Preferir alinhamento à esquerda para textos e títulos.
- Exibir números com separadores e unidades consistentes.
- Evitar mais de três níveis tipográficos na mesma área.

## 6. Componentes

### Menu lateral

- Dimensão: `190 × 720 px`.
- Fundo: `Navigation`.
- Logo ou nome do projeto no topo.
- Item ativo com fundo azul de baixa intensidade ou indicador lateral azul.
- Ícone e texto alinhados horizontalmente.
- Páginas previstas: Visão Executiva, Produtos, Clientes, Territórios, Vendedores e Ofertas.

### Cabeçalho

- Altura recomendada: `64 px`.
- Título da página à esquerda.
- Contexto ou período analisado abaixo ou ao lado do título.
- Filtros principais alinhados à direita.
- Evitar uma faixa de cor preenchendo toda a largura.

### Filtros

- Altura: `36 px`.
- Fundo branco e borda `Border`.
- Raio: `8 px`.
- Rótulo sempre visível.
- Filtros prioritários da Visão Executiva: período, território e canal.
- Limitar a quantidade de filtros aparentes; opções secundárias podem ficar em um painel recolhível.

### Cards de KPI

- Fundo branco.
- Raio: `10 px`.
- Borda: `1 px` em `Border`.
- Sombra leve e opcional; evitar sombras fortes.
- Padding interno: `16 px`.
- Ordem visual: rótulo, valor, comparação e contexto.
- Cinco KPIs iniciais: Receita líquida, Pedidos, Itens vendidos, Ticket médio e Desconto concedido.
- Usar a cor semântica apenas na variação ou no pequeno elemento de destaque.

### Cards analíticos

- Título no canto superior esquerdo.
- Subtítulo curto apenas quando necessário.
- Área do gráfico sem molduras internas desnecessárias.
- Legenda próxima ao dado e limitada às séries relevantes.
- Menu de opções no canto superior direito somente quando houver função real.

### Tooltips

- Fundo branco, borda discreta e texto escuro.
- Mostrar valor, período, categoria e comparação relevante.
- Evitar repetir informações já visíveis no gráfico.

## 7. Gráficos

### Princípios gerais

- Cada visual deve responder a uma pergunta de negócio explícita.
- Títulos devem descrever a análise, por exemplo: “Receita líquida ao longo do tempo”.
- Começar eixos de barras em zero.
- Evitar gráficos 3D, medidores decorativos e excesso de linhas de grade.
- Ordenar categorias por valor quando a ordem natural não for relevante.
- Exibir rótulos somente quando melhorarem a leitura.

### Aplicação na Visão Executiva

| Pergunta | Visual recomendado |
| --- | --- |
| Como as vendas evoluíram? | linha ou área leve por mês |
| Quais territórios mais contribuem? | barras horizontais |
| Como a receita se distribui por categoria? | barras ou treemap com poucas categorias |
| Qual a participação de vendas online e assistidas? | barras 100% empilhadas ou donut simples |

O gráfico de evolução deve ocupar a maior área, pois representa a leitura principal da página.

## 8. Estrutura da página Visão Executiva

1. Menu lateral fixo.
2. Cabeçalho com título, período e filtros.
3. Linha com cinco cards de KPI.
4. Área principal com evolução mensal da receita.
5. Área secundária com território e categoria.
6. Comparação entre vendas online e assistidas.
7. Rodapé discreto com data da última atualização.

## 9. Formatação de dados

| Tipo | Padrão |
| --- | --- |
| Moeda | `R$ 1,2 mi` nos cards; valor completo no tooltip |
| Quantidade | `12,3 mil` quando necessário |
| Percentual | uma casa decimal, como `12,4%` |
| Data curta | `dd/mm/aaaa` |
| Mês | `jan/2026` |
| Valor ausente | `—` |

Os dados do AdventureWorks podem estar em outra moeda. Nesse caso, substituir o símbolo de forma global e registrar a moeda no dashboard; nunca misturar moedas sem identificação.

## 10. Acessibilidade

- Garantir contraste suficiente entre texto e fundo.
- Não usar fonte menor que 10 px.
- Não comunicar estado exclusivamente por vermelho e verde.
- Manter títulos e rótulos objetivos.
- Definir texto alternativo nos visuais do Power BI.
- Organizar a ordem de tabulação dos componentes.
- Evitar interações que dependam apenas de hover.

## 11. Padrões para Figma e Power BI

### No Figma

- Criar uma página chamada `Design System`.
- Transformar menu, filtros, KPI cards e cards analíticos em componentes.
- Utilizar estilos de cor e texto com os nomes dos tokens deste documento.
- Nomear camadas e componentes de maneira funcional.

### No Power BI

- Construir gráficos, cartões, filtros e botões como elementos funcionais.
- Usar imagens ou SVG apenas para recursos decorativos e ícones.
- Evitar exportar o dashboard inteiro do Figma como uma única imagem de fundo.
- Reproduzir tamanhos, alinhamentos e espaçamentos do protótipo.
- Manter medidas, relacionamentos e definições no projeto PBIP versionado pelo Git.

## 12. Critérios de validação

Antes de considerar uma página concluída, verificar:

- o propósito da página está claro em poucos segundos;
- os KPIs mais importantes aparecem primeiro;
- as cores seguem significado consistente;
- os elementos estão alinhados à grade;
- filtros e interações são previsíveis;
- o layout pode ser reproduzido no Power BI;
- números, datas e unidades estão padronizados;
- o conteúdo continua legível sem depender apenas das cores.

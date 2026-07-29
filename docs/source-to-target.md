# Mapeamento inicial — Vendas

## Grão do fato

A tabela `analytics.fact_sales` terá uma linha por item de pedido de venda,
identificado pela combinação de `sales_order_id` e `sales_order_detail_id`.

## Tabelas de origem

| Tabela AdventureWorks | Finalidade | Destino principal |
| --- | --- | --- |
| `sales.salesorderheader` | datas, cliente, território, frete e total do pedido | `fact_sales` |
| `sales.salesorderdetail` | produto, quantidade, preço e desconto do item | `fact_sales` |
| `sales.customer` | identificação do cliente | `dim_customer` |
| `person.person` | nome do cliente pessoa física | `dim_customer` |
| `sales.store` | nome do cliente corporativo | `dim_customer` |
| `production.product` | produto, custo e atributos comerciais | `dim_product` |
| `production.productsubcategory` | subcategoria do produto | `dim_product` |
| `production.productcategory` | categoria do produto | `dim_product` |
| `sales.salesterritory` | região comercial | `dim_sales_territory` |

## Modelo de destino

### `analytics.fact_sales`

- `sales_order_id`
- `sales_order_detail_id`
- `order_date_key`
- `customer_key`
- `product_key`
- `sales_territory_key`
- `order_quantity`
- `unit_price`
- `unit_price_discount`
- `gross_amount`
- `discount_amount`
- `net_amount`
- `standard_cost`
- `gross_margin`

### Dimensões

- `analytics.dim_date`
- `analytics.dim_customer`
- `analytics.dim_product`
- `analytics.dim_sales_territory`

## Regras iniciais

```text
gross_amount   = order_quantity * unit_price
discount_amount = gross_amount * unit_price_discount
net_amount     = gross_amount - discount_amount
standard_cost  = order_quantity * product.standardcost
gross_margin   = net_amount - standard_cost
```

Frete e impostos pertencem ao cabeçalho do pedido. Eles não serão rateados
entre os itens no MVP; essa decisão evita atribuir custos de forma arbitrária.

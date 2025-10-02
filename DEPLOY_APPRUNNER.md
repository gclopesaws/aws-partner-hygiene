# 🚀 Deploy AWS App Runner - Guia Rápido

## ⚡ Deploy em 2 Comandos

```bash
# 1. Executar deploy
./deploy-apprunner.sh deploy

# 2. Verificar status
./deploy-apprunner.sh status
```

## 📋 Pré-requisitos

1. **AWS CLI** instalado e configurado
2. **Permissões** para criar recursos App Runner e IAM
3. **Repositório GitHub** público (já configurado)

### Configurar AWS CLI (se necessário)
```bash
aws configure
# AWS Access Key ID: [sua-key]
# AWS Secret Access Key: [sua-secret]
# Default region: us-east-1
# Default output format: json
```

## 🎯 Processo de Deploy

### 1. Executar Deploy
```bash
./deploy-apprunner.sh deploy
```

**O que acontece:**
- ✅ Cria IAM Role para App Runner
- ✅ Configura Auto Scaling (1-5 instâncias)
- ✅ Conecta ao GitHub automaticamente
- ✅ Configura build e start commands
- ✅ Configura health checks
- ✅ Cria logs no CloudWatch

### 2. Aguardar Build (5-10 minutos)
O App Runner vai:
- Fazer clone do repositório
- Instalar dependências (`pip install -r streamlit_app/requirements_web.txt`)
- Iniciar Streamlit na porta 8080
- Configurar HTTPS automaticamente

### 3. Acessar Aplicação
Após o deploy, você receberá uma URL como:
```
https://abc123def456.us-east-1.awsapprunner.com
```

## 🔧 Comandos Disponíveis

```bash
# Deploy inicial ou atualização
./deploy-apprunner.sh deploy

# Verificar status e URL
./deploy-apprunner.sh status

# Deletar todos os recursos
./deploy-apprunner.sh delete

# Mostrar menu de ajuda
./deploy-apprunner.sh
```

## 📊 Configurações do Deploy

| Configuração | Valor | Descrição |
|--------------|-------|-----------|
| **Instância** | 0.5 vCPU, 1 GB | Balanceado custo/performance |
| **Auto Scaling** | 1-5 instâncias | Escala conforme demanda |
| **Concorrência** | 20 requests/instância | Otimizado para Streamlit |
| **Health Check** | `/_stcore/health` | Endpoint padrão Streamlit |
| **Logs** | 14 dias retenção | CloudWatch Logs |

## 💰 Custos Estimados

- **Instância 0.5 vCPU, 1 GB:** ~$30-50/mês
- **Tráfego:** Incluído até 100 GB/mês
- **Build time:** ~$0.005/minuto (apenas durante builds)

## 🔄 Auto Deploy

**Qualquer push para o branch `main` fará deploy automático!**

```bash
# Fazer mudanças no código
git add .
git commit -m "Nova funcionalidade"
git push origin main

# App Runner detecta automaticamente e faz novo deploy
```

## 🛠️ Troubleshooting

### Build falha
```bash
# Ver logs detalhados
aws logs tail /aws/apprunner/aws-partner-hygiene --follow --region us-east-1
```

### Aplicação não carrega
1. Verificar se health check está passando
2. Verificar se porta 8080 está configurada
3. Verificar logs de runtime

### Erro de permissões
```bash
# Verificar se usuário tem permissões necessárias
aws iam get-user
aws apprunner list-services --region us-east-1
```

## 📱 Monitoramento

### Console AWS
- **App Runner:** https://console.aws.amazon.com/apprunner/
- **CloudWatch:** https://console.aws.amazon.com/cloudwatch/

### CLI Commands
```bash
# Status do serviço
aws apprunner describe-service --service-arn [ARN] --region us-east-1

# Logs em tempo real
aws logs tail /aws/apprunner/aws-partner-hygiene --follow --region us-east-1

# Métricas
aws cloudwatch get-metric-statistics \
  --namespace AWS/AppRunner \
  --metric-name RequestCount \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## 🔒 Segurança

- ✅ **HTTPS automático** com certificado gerenciado
- ✅ **IAM roles** com permissões mínimas
- ✅ **VPC isolamento** (opcional)
- ✅ **Logs criptografados** no CloudWatch

## 🚀 Próximos Passos

1. **Testar aplicação** na URL fornecida
2. **Configurar domínio customizado** (opcional)
3. **Configurar alertas** CloudWatch
4. **Otimizar performance** conforme uso

---

**Status:** ✅ **PRONTO PARA DEPLOY**  
**Tempo:** ⏱️ **5-10 minutos**  
**Custo:** 💰 **~$30-50/mês**
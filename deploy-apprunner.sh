#!/bin/bash

# Deploy script para AWS App Runner
# AWS Partner Pipeline Analysis

set -e

# Configurações
STACK_NAME="aws-partner-hygiene-apprunner"
REGION="us-east-1"  # Altere se necessário
TEMPLATE_FILE="cloudformation-apprunner-file-config.yaml"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AWS Partner Pipeline Analysis - App Runner Deploy${NC}"
echo "========================================================="

# Verificar se AWS CLI está configurado
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI não encontrado. Instale o AWS CLI primeiro.${NC}"
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS CLI não está configurado. Execute 'aws configure' primeiro.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ AWS CLI configurado${NC}"
    
    # Mostrar informações da conta
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
    echo -e "${BLUE}📋 Conta AWS: ${ACCOUNT_ID}${NC}"
    echo -e "${BLUE}👤 Usuário: ${USER_ARN}${NC}"
}

# Função de deploy
deploy() {
    echo -e "${YELLOW}📦 Iniciando deploy do App Runner...${NC}"
    echo ""
    echo "Configurações:"
    echo "• Stack: $STACK_NAME"
    echo "• Região: $REGION"
    echo "• Repositório: https://github.com/gclopesaws/aws-partner-hygiene"
    echo "• Branch: main"
    echo ""
    
    read -p "Continuar com o deploy? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo -e "${YELLOW}Deploy cancelado.${NC}"
        exit 0
    fi
    
    echo -e "${YELLOW}🔨 Executando CloudFormation deploy...${NC}"
    
    aws cloudformation deploy \
        --template-file "$TEMPLATE_FILE" \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            AppName="aws-partner-hygiene" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION" \
        --no-fail-on-empty-changeset
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Deploy concluído com sucesso!${NC}"
        
        # Obter URL da aplicação
        echo -e "${YELLOW}🔍 Obtendo URL da aplicação...${NC}"
        SERVICE_URL=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`AppRunnerServiceUrl`].OutputValue' \
            --output text 2>/dev/null)
        
        if [ -n "$SERVICE_URL" ] && [ "$SERVICE_URL" != "None" ]; then
            echo ""
            echo -e "${GREEN}🎉 Aplicação deployada com sucesso!${NC}"
            echo -e "${BLUE}🌐 URL: $SERVICE_URL${NC}"
            echo -e "${YELLOW}💰 Custo estimado: $30-50/mês${NC}"
            echo ""
            echo -e "${BLUE}📋 Próximos passos:${NC}"
            echo "1. Aguarde 5-10 minutos para o App Runner fazer o build"
            echo "2. Acesse a URL acima para testar a aplicação"
            echo "3. Qualquer push para o branch 'main' fará deploy automático"
            echo ""
            echo -e "${BLUE}📊 Monitoramento:${NC}"
            echo "• Console AWS App Runner: https://console.aws.amazon.com/apprunner/"
            echo "• CloudWatch Logs: /aws/apprunner/aws-partner-hygiene"
        else
            echo -e "${YELLOW}⚠️  Deploy concluído, mas URL não disponível ainda.${NC}"
            echo "Verifique o console AWS App Runner em alguns minutos."
        fi
    else
        echo -e "${RED}❌ Erro no deploy. Verifique os logs acima.${NC}"
        exit 1
    fi
}

# Função para verificar status
status() {
    echo -e "${BLUE}📊 Verificando status do App Runner...${NC}"
    
    # Verificar se stack existe
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &>/dev/null; then
        echo -e "${GREEN}✅ Stack encontrada${NC}"
        
        # Obter informações
        SERVICE_URL=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`AppRunnerServiceUrl`].OutputValue' \
            --output text 2>/dev/null)
        
        SERVICE_ARN=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`AppRunnerServiceArn`].OutputValue' \
            --output text 2>/dev/null)
        
        echo -e "${BLUE}🌐 URL: $SERVICE_URL${NC}"
        echo -e "${BLUE}📋 ARN: $SERVICE_ARN${NC}"
        
        # Verificar status do serviço
        if [ -n "$SERVICE_ARN" ]; then
            SERVICE_STATUS=$(aws apprunner describe-service \
                --service-arn "$SERVICE_ARN" \
                --region "$REGION" \
                --query 'Service.Status' \
                --output text 2>/dev/null)
            
            echo -e "${BLUE}📊 Status: $SERVICE_STATUS${NC}"
        fi
    else
        echo -e "${RED}❌ Stack não encontrada. Execute o deploy primeiro.${NC}"
    fi
}

# Função para deletar
delete() {
    echo -e "${RED}🗑️  Deletando recursos...${NC}"
    
    read -p "Tem certeza que deseja deletar todos os recursos? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo -e "${YELLOW}Operação cancelada.${NC}"
        exit 0
    fi
    
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
    
    echo -e "${GREEN}✅ Comando de deleção enviado. Recursos serão removidos em alguns minutos.${NC}"
}

# Menu principal
case "${1:-menu}" in
    "deploy")
        check_aws_cli
        deploy
        ;;
    "status")
        check_aws_cli
        status
        ;;
    "delete")
        check_aws_cli
        delete
        ;;
    "menu"|*)
        echo ""
        echo "Uso: $0 [comando]"
        echo ""
        echo "Comandos disponíveis:"
        echo "  deploy  - Fazer deploy da aplicação"
        echo "  status  - Verificar status da aplicação"
        echo "  delete  - Deletar todos os recursos"
        echo ""
        echo "Exemplos:"
        echo "  $0 deploy"
        echo "  $0 status"
        echo "  $0 delete"
        echo ""
        ;;
esac
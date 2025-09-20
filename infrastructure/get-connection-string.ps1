# Get Cosmos DB Connection String
$resourceGroup = "ecommerce-chat-rg"
$cosmosAccount = "ecommerce-chat-dev-cosmos"

Write-Host "🔗 Getting Cosmos DB Connection String..." -ForegroundColor Blue

try {
    $connectionString = az cosmosdb keys list --name $cosmosAccount --resource-group $resourceGroup --type connection-strings --query "connectionStrings[0].connectionString" --output tsv
    
    if ($connectionString) {
        Write-Host "✅ Connection String Retrieved:" -ForegroundColor Green
        Write-Host $connectionString -ForegroundColor Yellow
        
        # Store in Key Vault
        Write-Host "`n💾 Storing in Key Vault..." -ForegroundColor Blue
        $keyVaultName = "ecommerce-chat-dev-kv"
        
        az keyvault secret set --vault-name $keyVaultName --name "cosmos-db-connection-string" --value $connectionString
        
        Write-Host "✅ Connection string stored in Key Vault!" -ForegroundColor Green
        
        # Also save to file for easy access
        $connectionString | Out-File -FilePath "cosmos-connection-string.txt" -Encoding UTF8
        Write-Host "📄 Connection string also saved to cosmos-connection-string.txt" -ForegroundColor Cyan
        
    } else {
        Write-Host "❌ Failed to get connection string" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

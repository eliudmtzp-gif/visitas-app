# Script para automatizar git add, commit y push

Write-Host "Verificando cambios en el repositorio..."
git status

# Agregar todos los cambios
git add .

# Preguntar mensaje de commit
$mensaje = Read-Host "Escribe el mensaje de commit"
git commit -m "$mensaje"

# Mostrar estado después del commit
git status

# Confirmar push
$continuar = Read-Host "¿Quieres hacer git push? (s/n)"
if ($continuar -eq "s") {
    Write-Host "Ejecutando git push..."
    git push origin main
    Write-Host "Cambios subidos a GitHub."
} else {
    Write-Host "Operación cancelada."
}

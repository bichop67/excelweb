document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generateBtn');
    const promptTextarea = document.getElementById('prompt');
    const spinner = generateBtn.querySelector('.spinner-border');
    const errorDiv = document.getElementById('error');

    generateBtn.addEventListener('click', async function() {
        // Validation
        if (!promptTextarea.value.trim()) {
            showError("Veuillez entrer un prompt.");
            return;
        }

        // UI feedback
        startLoading();
        hideError();

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: promptTextarea.value
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 429 || errorData.error.includes("rate limit")) {
                    throw new Error("Limite d'utilisation de l'API atteinte. Veuillez réessayer dans quelques minutes.");
                } else if (response.status === 500) {
                    throw new Error(errorData.error || "Une erreur est survenue lors de la génération du fichier Excel.");
                } else {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
            }

            // Téléchargement du fichier
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'generated_excel.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

        } catch (error) {
            showError(error.message);
        } finally {
            stopLoading();
        }
    });

    function startLoading() {
        generateBtn.disabled = true;
        spinner.classList.remove('d-none');
        generateBtn.textContent = ' Génération en cours...';
        generateBtn.prepend(spinner);
    }

    function stopLoading() {
        generateBtn.disabled = false;
        spinner.classList.add('d-none');
        generateBtn.textContent = 'Générer Excel';
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('d-none');
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function hideError() {
        errorDiv.classList.add('d-none');
    }
});

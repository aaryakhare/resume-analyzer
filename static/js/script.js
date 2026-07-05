document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fileInput");
    const browseBtn = document.getElementById("browseBtn");
    const dropzone = document.getElementById("dropzone");
    const fileChosen = document.getElementById("fileChosen");
    const fileName = document.getElementById("fileName");
    const clearFile = document.getElementById("clearFile");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const jobDescription = document.getElementById("jobDescription");
    const errorMsg = document.getElementById("errorMsg");
    const ALLOWED_TYPES = [
        "pdf",
        "docx",
        "txt"
    ];
    const MAX_SIZE = 5 * 1024 * 1024;
    let selectedFile = null;
    function showError(message) {

        errorMsg.hidden = false;
        errorMsg.textContent = message;

    }
    function clearError() {

        errorMsg.hidden = true;
        errorMsg.textContent = "";

    }
    function validateFile(file) {

        if (!file)
            return false;

        const extension =
            file.name.split(".").pop().toLowerCase();

        if (!ALLOWED_TYPES.includes(extension)) {

            showError("Only PDF, DOCX and TXT files are allowed.");
            return false;

        }

        if (file.size > MAX_SIZE) {

            showError("Maximum file size is 5 MB.");
            return false;

        }

        return true;

    }
    function setFile(file) {

        clearError();

        if (!validateFile(file))
            return;

        selectedFile = file;

        fileName.textContent = file.name;

        fileChosen.hidden = false;

        dropzone.hidden = true;

        analyzeBtn.disabled = false;

    }
    function removeFile() {

        selectedFile = null;

        fileInput.value = "";

        dropzone.hidden = false;

        fileChosen.hidden = true;

        analyzeBtn.disabled = true;

    }
browseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
});
dropzone.addEventListener("click", () => {
    fileInput.click();
});
    fileInput.addEventListener("change", (e) => {

        if (e.target.files.length > 0) {

            setFile(e.target.files[0]);

        }

    });

    clearFile.addEventListener("click", (e) => {

        e.stopPropagation();

        removeFile();

    });
    ["dragenter", "dragover"].forEach(event => {

        dropzone.addEventListener(event, (e) => {

            e.preventDefault();

            dropzone.style.borderColor = "#b3362d";

        });

    });


    ["dragleave", "drop"].forEach(event => {

        dropzone.addEventListener(event, (e) => {

            e.preventDefault();

            dropzone.style.borderColor = "#c9ccd3";

        });

    });


    dropzone.addEventListener("drop", (e) => {

        if (e.dataTransfer.files.length > 0) {

            setFile(e.dataTransfer.files[0]);

        }

    });
    function setLoading(isLoading) {

        if (isLoading) {

            analyzeBtn.disabled = true;

            analyzeBtn.textContent = "Analyzing...";

        }

        else {

            analyzeBtn.disabled = false;

            analyzeBtn.textContent = "Analyze Resume";

        }

    } function createList(element, items) {
    element.innerHTML = "";

    if (!items || items.length === 0) {
        const li = document.createElement("li");
        li.textContent = "Nothing to show";
        element.appendChild(li);
        return;
    }

    items.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        element.appendChild(li);
    });
}

function createChips(element, words) {
    element.innerHTML = "";

    if (!words || words.length === 0) {
        const chip = document.createElement("span");
        chip.textContent = "None";
        element.appendChild(chip);
        return;
    }

    words.slice(0, 5).forEach(word => {
        const chip = document.createElement("span");
        chip.textContent = word;
        element.appendChild(chip);
    });
}
analyzeBtn.addEventListener("click", async () => {

    if (!selectedFile) {
        showError("Please choose a resume first.");
        return;
    }

    clearError();
    setLoading(true);

    const formData = new FormData();
    formData.append("resume", selectedFile);
    formData.append("job_description", jobDescription.value);

    try {

        const response = await fetch("/api/analyze", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.error || "Something went wrong.");
            return;
        }

        window.location.href = "/result";

    }

    catch (error) {

        console.error(error);
        showError("Unable to connect to server.");

    }

    finally {

        setLoading(false);

    }

});
});
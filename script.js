document.getElementById("generate-button").addEventListener("click", async () => {
    const jobDescription = document.getElementById("job-description").value;

    if (!jobDescription) {
        alert("Please paste a job description.");
        return;
    }

    const response = await fetch("/generate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ job_description: jobDescription }),
    });

    const data = await response.json();
    document.getElementById("cover-letter").value = data.cover_letter;
});

document.getElementById("copy-button").addEventListener("click", () => {
    const coverLetter = document.getElementById("cover-letter");
    coverLetter.select();
    document.execCommand("copy");
    alert("Cover letter copied to clipboard!");
});
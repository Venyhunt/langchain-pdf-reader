// app.js

document.addEventListener("DOMContentLoaded", () => {
  const askForm = document.getElementById("ask-form");
  const queryInput = document.getElementById("query-input");
  const collectionInput = document.getElementById("collection-input");
  const answerArea = document.getElementById("answer");
  const sourcesArea = document.getElementById("sources");
  const spinner = document.getElementById("spinner");

  askForm.addEventListener("submit", async (e) => {
    e.preventDefault(); // stop normal form reload

    const query = queryInput.value.trim();
    const collection = collectionInput.value || "";
    if (!query) return;

    spinner.style.display = "inline";
    answerArea.textContent = "";
    sourcesArea.textContent = "";

    try {
      // Send the question to Flask as JSON
      const res = await fetch("/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        body: JSON.stringify({ query, collection }),
      });

      let data;
    try {
        data = await res.json();
    } catch (err) {
    console.log("Server response (not JSON):", await res.text());
    return; // stop further execution
        }

      

      if (!res.ok) {
        answerArea.textContent = data.error || "Server error occurred.";
      } else {
        // Display the answer
        answerArea.innerHTML = `<h3>Answer</h3><div>${data.answer || "No answer"}</div>`;

        // Display the sources
        if (data.sources && data.sources.length > 0) {
          const ul = document.createElement("ul");
          data.sources.forEach((src) => {
            const li = document.createElement("li");
            li.innerHTML = `<pre style="white-space: pre-wrap;">${src.snippet || ""}</pre>`;
            ul.appendChild(li);
          });
          sourcesArea.innerHTML = "<h4>Sources</h4>";
          sourcesArea.appendChild(ul);
        }
      }
    } catch (err) {
      answerArea.textContent = "Error contacting server: " + err.message;
    } finally {
      spinner.style.display = "none";
    }
  });

});
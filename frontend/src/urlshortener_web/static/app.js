const copyButton = document.querySelector("[data-short-url]");
if (copyButton) {
  copyButton.addEventListener("click", async () => {
    const value = copyButton.getAttribute("data-short-url");
    if (!value || !navigator.clipboard) {
      return;
    }
    try {
      await navigator.clipboard.writeText(value);
    } catch (_clipboardError) {
      const field = document.createElement("textarea");
      field.value = value;
      document.body.appendChild(field);
      field.select();
      const copied = document.execCommand("copy");
      field.remove();
      if (!copied) {
        return;
      }
    }
    copyButton.textContent = "Copied";
    copyButton.classList.add("is-copied");
  });
}

let registerMode = false;

const form = document.getElementById("authForm");
const button = document.getElementById("authBtn");
const toggle = document.getElementById("toggleAuth");
const errorBox = document.getElementById("authError");


toggle.addEventListener("click", () => {

    registerMode = !registerMode;

    if (registerMode) {

        button.textContent = "Register";

        toggle.textContent =
            "Already have an account? Login";

    } else {

        button.textContent = "Login";

        toggle.textContent =
            "Need an account? Register";

    }

    errorBox.textContent = "";

});


form.addEventListener("submit", async (event) => {

    event.preventDefault();

    errorBox.textContent = "";

    const formData = new FormData(form);

    const endpoint = registerMode
        ? "/api/register"
        : "/api/login";

    try {

        const response = await fetch(
            endpoint,
            {
                method: "POST",
                body: formData,
            }
        );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Request failed."
            );

        }

        window.location.href = "/";

    } catch (error) {

        errorBox.textContent =
            error.message;

    }

});
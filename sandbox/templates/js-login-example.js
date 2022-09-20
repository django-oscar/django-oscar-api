const base_url = "http://localhost:8000/"

const getCookie = (name) => {
    let value = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim()
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                value = decodeURIComponent(cookie.substring(name.length + 1))
                break
            }
        }
    }
    return value
}

const login = (username, password) => {
    return fetch(base_url + "api/login/", {
        method:"POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
}

const logout = () => {
    return fetch(base_url + "api/login/", {
        method:"DELETE",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken")
        }
    })
}


const basket = () => {
    return fetch(base_url + "api/basket/", {
        method:"GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        }
    })
}

window.addEventListener('DOMContentLoaded',function () {
    document.querySelector("#login").onclick = () => {
        const username = document.querySelector("#username").value
        const password = document.querySelector("#password").value

        login(username, password).then((response) => {
            if(response.status === 200) {
                return basket()
            }
            return response
        })
        .then((response) => response.json())
        .then((result) => {
            document.querySelector("#output").innerHTML = JSON.stringify(result, null, 4);
        })
        .catch(err => {
            console.error(err);
        });
    }

    document.querySelector("#logout").onclick = () => {
        logout()
        .then((response) => response.json())
        .then((result) => {
            document.querySelector("#output").innerHTML = JSON.stringify(result, null, 4);
        })
    }

    document.querySelector("#fetch-basket").onclick = () => {
        basket()
        .then((response) => response.json())
        .then((result) => {
            document.querySelector("#output").innerHTML = JSON.stringify(result, null, 4);
        })
    }

  })
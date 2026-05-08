export async function api(path, options = {}) {
    const response = await fetch(path, options);

    return response.json();
}

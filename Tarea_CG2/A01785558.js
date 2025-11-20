/*
    Santiago Coronado Hernández A01785558
    20-11-2025
    Tarea CG 2: Genera Archivo OBJ de una figura 3D
*/

import fs from 'fs'; // Usamos fs para escribir el archivo

function main() {
    // Agarra inputs
    const args = process.argv.slice(2);
    const sides = parseInt(args[0]) || 8; 
    const height = parseFloat(args[1]) || 6.0; 
    const baseRadius = parseFloat(args[2]) || 1.0; 
    const topRadius = parseFloat(args[3]) || 0.8; 

    if (sides < 3 || sides > 36 || height <= 0 || baseRadius <= 0 || topRadius <= 0) {
        console.error("Error: Argumentos inválidos. Asegúrate de que:");
        console.error("- Número de lados esté entre 3 y 36.");
        console.error("- Altura, radio de la base y radio de la cima sean positivos.");
        return;
    }

    // Genera archivo OBJ
    const objData = generateOBJFile(sides, height, baseRadius, topRadius);

    // Escribe el archivo OBJ
    fs.writeFileSync('Figura_TareaCG2.obj', objData);
    console.log("Archivo OBJ generado: Figura_TareaCG2.obj");
}

function generateOBJFile(sides, height, baseRadius, topRadius) {
    let vertices = [];
    let faces = [];

    // Generar vertices para la base
    vertices.push(`v 0 0 0`); // Centro de la base
    let angleStep = (2 * Math.PI) / sides;

    for (let s = 0; s < sides; s++) {
        let angle = angleStep * s;
        let x = Math.cos(angle) * baseRadius;
        let y = Math.sin(angle) * baseRadius;
        vertices.push(`v ${x} ${0} ${y}`); // Vertices de la base
    }

    // Genera vertices para la cima
    vertices.push(`v 0 ${height} 0`); // Centro de la cima
    for (let s = 0; s < sides; s++) {
        let angle = angleStep * s;
        let x = Math.cos(angle) * topRadius;
        let y = Math.sin(angle) * topRadius;
        vertices.push(`v ${x} ${height} ${y}`); // Vertices de la cima
    }

    // Generar caras para la base
    for (let s = 1; s <= sides; s++) {
        let next = (s % sides) + 1;
        faces.push(`f 1 ${s + 1} ${next + 1}`);
    }

    // Genera caras para la cima
    let topCenterIndex = sides + 2;
    for (let s = 1; s <= sides; s++) {
        let next = (s % sides) + 1;
        faces.push(`f ${topCenterIndex} ${topCenterIndex + s} ${topCenterIndex + next}`);
    }

    // Genera caras para los lado
    for (let s = 1; s <= sides; s++) {
        let next = (s % sides) + 1;
        let baseVertex = s + 1;
        let topVertex = topCenterIndex + s;
        let nextBaseVertex = next + 1;
        let nextTopVertex = topCenterIndex + next;

        faces.push(`f ${baseVertex} ${nextBaseVertex} ${topVertex}`);
        faces.push(`f ${nextBaseVertex} ${nextTopVertex} ${topVertex}`);
    }

    // Combinar vertices y caras en OBJ
    return vertices.join('\n') + '\n' + faces.join('\n');
}

main();
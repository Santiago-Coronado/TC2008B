/*
 * Script to draw a complex shape in 2D
 *
 * Gilberto Echeverria
 * 2024-07-12
 */


'use strict';

import * as twgl from 'twgl-base.js';
import { M3 } from '../2d-lib.js';
import GUI from 'lil-gui';

// Define the shader code, using GLSL 3.00

const vsGLSL = `#version 300 es
in vec2 a_position;
in vec4 a_color;

uniform vec2 u_resolution;
uniform mat3 u_transforms;

out vec4 v_color;

void main() {
    // Multiply the matrix by the vector, adding 1 to the vector to make
    // it the correct size. Then keep only the two first components
    vec2 position = (u_transforms * vec3(a_position, 1)).xy;

    // Convert the position from pixels to 0.0 - 1.0
    vec2 zeroToOne = position / u_resolution;

    // Convert from 0->1 to 0->2
    vec2 zeroToTwo = zeroToOne * 2.0;

    // Convert from 0->2 to -1->1 (clip space)
    vec2 clipSpace = zeroToTwo - 1.0;

    // Invert Y axis
    //gl_Position = vec4(clipSpace[0], clipSpace[1] * -1.0, 0, 1);
    gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);
    v_color = a_color;
}
`;

const fsGLSL = `#version 300 es
precision highp float;

in vec4 v_color;

out vec4 outColor;

void main() {
    outColor = v_color;
}
`;


// Structure for the global data of all objects
// This data will be modified by the UI and used by the renderer
const objects = {
    model: {
        transforms: {
            t: {
                x: 0,
                y: 0,
                z: 0,
            },
            rr: {
                x: 0,
                y: 0,
                z: 0,
            },
            s: {
                x: 1,
                y: 1,
                z: 1,
            }
        },
        color: [1, 0.3, 0, 1],
    },
    pivote: {
        transforms: {
            t: {
                x: 0,
                y: 0,
                z: 0,
            }
        },
        color: [1, 0.3, 0, 1],
    }
}

// Initialize the WebGL environmnet
function main() {
    const canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl2');
    twgl.resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    setupUI(gl);

    const programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);

    // Crear buffer para la figura principal
    const arrays = Figura();
    const bufferInfo = twgl.createBufferInfoFromArrays(gl, arrays);
    const vao = twgl.createVAOFromBufferInfo(gl, programInfo, bufferInfo);

    // Crear buffer para el pivote
    const arraysPivote = Pivote();
    const bufferInfoPivote = twgl.createBufferInfoFromArrays(gl, arraysPivote);
    const vaoPivote = twgl.createVAOFromBufferInfo(gl, programInfo, bufferInfoPivote);

    drawScene(gl, vao, programInfo, bufferInfo, vaoPivote, bufferInfoPivote);
}

function drawScene(gl, vao, programInfo, bufferInfo, vaoPivote, bufferInfoPivote) {
    gl.useProgram(programInfo.program);

    // Dibujar Pivote
    let translatePivote = [objects.pivote.transforms.t.x, objects.pivote.transforms.t.y];
    const traMatPivote = M3.translation(translatePivote);

    let transformsPivote = M3.identity();
    transformsPivote = M3.multiply(traMatPivote, transformsPivote);

    let uniformsPivote = {
        u_resolution: [gl.canvas.width, gl.canvas.height],
        u_transforms: transformsPivote,
        u_color: objects.pivote.color,
    };

    twgl.setUniforms(programInfo, uniformsPivote);
    gl.bindVertexArray(vaoPivote);
    twgl.drawBufferInfo(gl, bufferInfoPivote);

    // Dibujar la figura principal
    let translate = [objects.model.transforms.t.x, objects.model.transforms.t.y];
    let angle_radians = objects.model.transforms.rr.z;
    let scale = [objects.model.transforms.s.x, objects.model.transforms.s.y];

    // Transformaciones
    const traToPivote = M3.translation([-objects.pivote.transforms.t.x, -objects.pivote.transforms.t.y]); // Trasladar a origen del pivote
    const rotMat = M3.rotation(angle_radians);
    const scaMat = M3.scale(scale);
    const traBackFromPivote = M3.translation([objects.pivote.transforms.t.x, objects.pivote.transforms.t.y]); // Regresar a posicion original
    const traMat = M3.translation(translate);

    // Combinar transformaciones en el orden correcto
    let finalTransforms = M3.identity();
    finalTransforms = M3.multiply(traMat, finalTransforms);           // Traslación independiente
    finalTransforms = M3.multiply(traToPivote, finalTransforms);      // Mover de vuelta desde el origen al pivote
    finalTransforms = M3.multiply(rotMat, finalTransforms);           // Rotar alrededor del pivote
    finalTransforms = M3.multiply(scaMat, finalTransforms);           // Escalar
    finalTransforms = M3.multiply(traBackFromPivote, finalTransforms); // Llevar pivote a origen

    let uniforms = {
        u_resolution: [gl.canvas.width, gl.canvas.height],
        u_transforms: finalTransforms,
        u_color: objects.model.color,
    };

    twgl.setUniforms(programInfo, uniforms);
    gl.bindVertexArray(vao);
    twgl.drawBufferInfo(gl, bufferInfo);

    requestAnimationFrame(() => drawScene(gl, vao, programInfo, bufferInfo, vaoPivote, bufferInfoPivote));
}


function setupUI(gl)
{
    const gui = new GUI();

    // Controles para la figura principal
    const modelFolder = gui.addFolder('Model');
    const traFolder = modelFolder.addFolder('Translation');
    traFolder.add(objects.model.transforms.t, 'x', -gl.canvas.width, gl.canvas.width);
    traFolder.add(objects.model.transforms.t, 'y', -gl.canvas.height, gl.canvas.height);

    const rotFolder = modelFolder.addFolder('Rotation');
    rotFolder.add(objects.model.transforms.rr, 'z', 0, Math.PI * 2);

    const scaFolder = modelFolder.addFolder('Scale');
    scaFolder.add(objects.model.transforms.s, 'x', -5, 5);
    scaFolder.add(objects.model.transforms.s, 'y', -5, 5);

    modelFolder.addColor(objects.model, 'color');


    // Controles para el pivote
    const pivoteFolder = gui.addFolder('Pivote');
    const traFolderPivote = pivoteFolder.addFolder('Translation');
    traFolderPivote.add(objects.pivote.transforms.t, 'x', 0, gl.canvas.width);
    traFolderPivote.add(objects.pivote.transforms.t, 'y', 0, gl.canvas.height);

    pivoteFolder.addColor(objects.pivote, 'color');
}

// Mitad x = 575 mitad y = 297
// cuadro de 40x20
function Figura() {
    return {
        a_position: {
            numComponents: 2,
            data: [
                // Centro arriba
                475, 107,   
                675, 107,   
                475, 137, 

                475, 137,
                675, 107,
                675, 137,

                // Extremo izquierdo
                375, 207,
                375, 307,
                405, 307,

                375, 207,
                405, 307,
                405, 207,

                // Extremo derecho
                745, 207,
                745, 307,
                775, 307,

                745, 207,
                775, 307,
                775, 207,

                // Centro abajo
                475, 377,
                675, 377,
                475, 407,

                475, 407,
                675, 377,
                675, 407,

                // Franja izquierda
                405, 257,
                405, 287,
                515, 287,

                405, 257,
                515, 287,
                515, 257,

                // Franja derecha
                635, 257,
                635, 287,
                755, 287,

                635, 257,
                755, 287,
                755, 257,

                // borde abajo izquierda
                475, 377,
                475, 347,
                450, 347,

                475, 377,
                450, 347,
                450, 377,

                450, 347,
                450, 327,
                405, 327,

                450, 347,
                405, 327,
                405, 347,

                405, 327,
                405, 307,
                422.5, 307,

                405, 327,
                422.5, 307,
                422.5, 327,

                // borde abajo derecha
                675, 377,
                675, 347,
                700, 347,

                675, 377,
                700, 347,
                700, 377,

                700, 347,
                700, 327,
                745, 327,

                700, 347,
                745, 327,
                745, 347,

                725, 327,
                725, 307,
                745, 307,

                725, 327,
                745, 307,
                745, 327,

                // borde arriba izquierda
                475, 167,
                475, 137,
                450, 137,

                475, 167,
                450, 137,
                450, 167,

                450, 167,
                450, 187,
                405, 187,

                450, 167,
                405, 187,
                405, 167,

                405, 187,
                405, 207,
                422.5, 207,

                405, 187,
                422.5, 207,
                422.5, 187,

                // borde arriba derecha
                675, 167,
                675, 137,
                700, 137,

                675, 167,
                700, 137,
                700, 167,

                700, 167,
                700, 187,
                745, 187,

                700, 167,
                745, 187,
                745, 167,

                725, 187,
                725, 207,
                745, 207,

                725, 187,
                745, 207,
                745, 187,

                // circulo centro
                515, 227,
                515, 287,
                545, 227,

                545, 227,
                515, 287,
                545, 287,

                635, 227,
                635, 287,
                605, 227,

                605, 227,
                635, 287,
                605, 287,

                545, 227,
                605, 227,
                545, 197,

                545, 197,
                605, 227,
                605, 197,

                545, 287,
                605, 287,
                545, 317,

                545, 317,
                605, 287,
                605, 317,

                // relleno rojo
                475, 137,   
                675, 137,   
                475, 167, 

                475, 167,
                675, 137,
                675, 167,

                450, 167,   
                700, 167,   
                450, 197, 

                450, 197,
                700, 167,
                700, 197,

                422.5, 197,   
                545, 197,   
                422.5, 227, 

                422.5, 227,
                545, 197,
                545, 227,

                422.5, 186,   
                450, 186,   
                422.5, 197, 

                422.5, 197,
                450, 186,
                450, 197,

                405, 207,
                405, 257,
                422.5, 207,

                422.5, 207,
                405, 257,
                422.5, 257,

                422.5, 227,
                515, 227,
                422.5, 257,

                422.5, 257,
                515, 227,
                515, 257,

                605, 197,
                725, 197,
                605, 227,

                605, 227,
                725, 197,
                725, 227,

                725, 187,
                698, 187,
                725, 197,

                725, 197,
                698, 187,
                698, 197,

                635, 227,
                745, 227,
                635, 257,

                635, 257,
                745, 227,
                745, 257,

                745, 227,
                724, 227,
                745, 207,

                745, 207,
                724, 227,
                724, 207,

                // relleno blanco
                545, 227,
                545, 287,
                605, 227,

                605, 227,
                545, 287,
                605, 287,

                475, 377,
                675, 377,
                475, 347,

                475, 347,
                675, 377,
                675, 347,

                405, 287,
                405, 307,
                545, 287,

                405, 307,
                545, 287,
                545, 307,

                605, 287,
                605, 307,
                745, 287,

                605, 307,
                745, 287,
                745, 307,

                450, 347,
                700, 347,
                450, 317,

                450, 317,
                700, 347,
                700, 317,

                422.5, 307,
                450, 307,
                422.5, 327,

                450, 307,
                422.5, 327,
                450, 327,

                725, 307,
                700, 307,
                725, 327,

                700, 307,
                725, 327,
                700, 327,

                450, 317,
                545, 317,
                450, 307,

                545, 317,
                450, 307,
                545, 307,

                605, 317,
                705, 317,
                605, 307,

                705, 317,
                605, 307,
                705, 307,
            ]
        },
        a_color: {
            numComponents: 4,
            data: [
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,
                0, 0, 0, 1,

                // relleno rojo
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,

                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,

                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,

                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,

                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,

                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,

                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,

                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,

                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,

                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,
                1, 0, 0, 1,

                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,

                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,

                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,

                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,

                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,

                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,

                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,

                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,

                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
                255, 255, 255, 1,
            ]
        }
    };
}

function Pivote() {
    return {
        a_position: {
            numComponents: 2,
            data: [
                0, 50,
                50, -50,
                -50, -50,
            ]
        },
        a_color: {
            numComponents: 4,
            data: [
                1, 1, 0, 1,
                1, 1, 0, 1,
                1, 1, 0, 1,
            ]
        }
    };
}

main()

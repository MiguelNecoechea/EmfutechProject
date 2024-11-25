class DataViewer {
    constructor() {
        console.log('DataViewer constructor called');
        if (typeof Plotly === 'undefined') {
            console.error('Plotly is not loaded!');
            document.body.innerHTML = '<div class="error">Error: Plotly library not available</div>';
            return;
        }
        this.participantData = null;
        this.initializeUI();
        
        if (!window.electronAPI) {
            console.error('electronAPI is not available!');
            document.body.innerHTML = '<div class="error">Error: Electron API not available</div>';
            return;
        }
        
        // Listen for the initialization data
        window.electronAPI.onInitDataViewer((data) => {
            console.log('Received participant data in DataViewer:', data);
            this.participantData = data;
            this.displayParticipantInfo();
            this.loadInitialData();
        });
    }

    initializeUI() {
        console.log('Initializing UI');
    }

    displayParticipantInfo() {
        console.log('Displaying participant info:', this.participantData);
        if (!this.participantData) {
            console.error('No participant data available');
            return;
        }

        const infoDiv = document.getElementById('participant-info');
        if (!infoDiv) {
            console.error('participant-info element not found');
            return;
        }

        // Create a formatted display with only name and folder path
        const participantDetails = `
            <h2>Participant Details</h2>
            <div class="participant-details">
                <p><strong>Name:</strong> ${this.participantData.name}</p>
                <p><strong>Folder Path:</strong> ${this.participantData.folderPath}</p>
            </div>
            <div class="visualization-controls">
                <select id="data-type-selector">
                    <option value="gaze">Eye Tracking</option>
                    <option value="emotion">Emotion</option>
                    <option value="aura">AURA</option>
                    <option value="pointer">Mouse/Keyboard</option>
                </select>
                <button id="refresh-data">Refresh</button>
            </div>
        `;

        infoDiv.innerHTML = participantDetails;

        // Set up event listeners after creating the elements
        this.setupEventListeners();
    }

    setupEventListeners() {
        console.log('Setting up event listeners');  // Add debug log
        const selector = document.getElementById('data-type-selector');
        const refreshButton = document.getElementById('refresh-data');

        if (selector) {
            console.log('Found selector, adding change listener');  // Add debug log
            selector.addEventListener('change', (event) => {
                console.log('Selector changed to:', event.target.value);  // Add debug log
                this.loadData();
            });
        } else {
            console.error('data-type-selector not found');
        }
        
        if (refreshButton) {
            console.log('Found refresh button, adding click listener');  // Add debug log
            refreshButton.addEventListener('click', () => {
                console.log('Refresh button clicked');  // Add debug log
                this.loadData();
            });
        } else {
            console.error('refresh-data button not found');
        }

        window.electronAPI.onDataUpdate((data) => {
            this.updateVisualization(data);
        });
    }

    async loadInitialData() {
        await this.loadData();
    }

    async loadData() {
        const dataType = document.getElementById('data-type-selector').value;
        console.log('Loading data for type:', dataType);
        
        const visualizationArea = document.getElementById('visualization-area');
        visualizationArea.innerHTML = '';
        
        try {
            const response = await window.electronAPI.getParticipantData({
                folderPath: this.participantData.folderPath,
                dataType: dataType
            });

            if (response.status !== 'success') {
                throw new Error(response.message);
            }

            // Fix the file type mapping to match exactly what's in the file list
            const fileTypeMap = {
                gaze: 'gaze',
                emotion: 'emotions',  // Changed from emotion to emotions
                aura: 'aura',
                pointer: 'data'      // Changed from pointer_data to data
            };

            const fileType = fileTypeMap[dataType];
            console.log('Looking for file type:', fileType);
            
            const file = response.data.files.find(f => f.type === fileType);
            console.log('Found file:', file);
            
            if (!file) {
                throw new Error(`No ${dataType} data found`);
            }

            const csvData = await fetch(`file://${file.path}`);
            const csvText = await csvData.text();
            
            // Parse CSV and create structured data
            const rows = csvText.split('\n')
                .filter(row => row.trim())
                .map(row => row.split(',').map(cell => cell.trim()));

            const headers = rows[0];
            const structuredData = rows.slice(1).map(row => {
                const rowData = {};
                headers.forEach((header, index) => {
                    rowData[header] = row[index];
                });
                return rowData;
            });

            console.log('Parsed data:', {
                type: dataType,
                headers: headers,
                rowCount: structuredData.length,
                sampleRow: structuredData[0]
            });

            this.createVisualization(dataType, structuredData);
        } catch (error) {
            console.error('Error loading data:', error);
            visualizationArea.innerHTML = `<p class="error">Error loading data: ${error.message}</p>`;
        }
    }

    createVisualization(dataType, structuredData) {
        console.log(`Creating visualization for ${dataType} with ${structuredData.length} rows`);
        console.log('First row of data:', structuredData[0]);
        
        try {
            switch(dataType) {
                case 'gaze':
                    this.createGazeVisualization(structuredData);
                    break;
                case 'emotion':
                    this.createEmotionVisualization(structuredData);
                    break;
                case 'aura':
                    this.createAuraVisualization(structuredData);
                    break;
                case 'pointer':
                    this.createPointerVisualization(structuredData);
                    break;
                default:
                    throw new Error(`Unknown data type: ${dataType}`);
            }
        } catch (error) {
            console.error(`Error creating ${dataType} visualization:`, error);
            const visualizationArea = document.getElementById('visualization-area');
            visualizationArea.innerHTML = `
                <p class="error">Error creating visualization: ${error.message}</p>
            `;
        }
    }

    createGazeVisualization(data) {
        const screenWidth = window.screen.width || 1920;
        const screenHeight = window.screen.height || 1080;

        // More robust data parsing
        const parsedData = data
            .filter(d => d && d.x && d.y && d.timestamp) // Filter out invalid rows
            .map(d => ({
                timestamp: parseFloat(d.timestamp) || 0,
                x: Math.max(0, parseFloat(d.x) || 0),
                y: Math.max(0, parseFloat(d.y) || 0)
            }))
            .filter(d => !isNaN(d.x) && !isNaN(d.y) && !isNaN(d.timestamp)); // Remove any NaN values

        if (parsedData.length === 0) {
            const visualizationArea = document.getElementById('visualization-area');
            visualizationArea.innerHTML = '<p class="error">No valid gaze data found</p>';
            return;
        }

        const maxX = Math.max(...parsedData.map(d => d.x));
        const maxY = Math.max(...parsedData.map(d => d.y));
        const displayWidth = Math.max(screenWidth, maxX);
        const displayHeight = Math.max(screenHeight, maxY);

        const visualizationArea = document.getElementById('visualization-area');
        visualizationArea.innerHTML = `
            <div id="gaze-scatter" style="height: 400px; margin-bottom: 20px;"></div>
            <div id="gaze-heatmap" style="height: 400px;"></div>
        `;

        const scatterTrace = {
            x: parsedData.map(d => d.x),
            y: parsedData.map(d => d.y),
            mode: 'markers',
            type: 'scatter',
            marker: {
                size: 6,
                color: parsedData.map(d => d.timestamp),
                colorscale: 'Viridis',
                showscale: true
            },
            name: 'Gaze Points'
        };

        const heatmapTrace = {
            x: parsedData.map(d => d.x),
            y: parsedData.map(d => d.y),
            type: 'histogram2d',
            colorscale: [
                [0, 'rgba(0,0,0,0)'],
                [0.2, 'rgba(0,0,255,0.3)'],
                [0.4, 'rgba(0,255,255,0.5)'],
                [0.6, 'rgba(0,255,0,0.7)'],
                [0.8, 'rgba(255,255,0,0.8)'],
                [1.0, 'rgba(255,0,0,1)']
            ],
            nbinsx: 100,
            nbinsy: 100,
            name: 'Gaze Density',
            showscale: true,
            zsmooth: 'best'
        };

        const commonLayout = {
            xaxis: {
                title: 'X Position',
                range: [0, displayWidth],
                showgrid: true,
                gridcolor: 'rgba(128,128,128,0.2)',
                autorange: false,
                constrain: 'domain'
            },
            yaxis: {
                title: 'Y Position',
                range: [displayHeight, 0],
                showgrid: true,
                gridcolor: 'rgba(128,128,128,0.2)',
                scaleanchor: 'x',
                scaleratio: 1,
                autorange: false,
                constrain: 'domain'
            },
            hovermode: 'closest',
            showlegend: true,
            paper_bgcolor: 'white',
            plot_bgcolor: 'rgba(255,255,255,0.9)',
            margin: {
                l: 50,
                r: 50,
                t: 50,
                b: 50
            }
        };

        Plotly.newPlot('gaze-scatter', [scatterTrace], {
            ...commonLayout,
            title: 'Eye Gaze Positions'
        });

        Plotly.newPlot('gaze-heatmap', [heatmapTrace], {
            ...commonLayout,
            title: 'Eye Gaze Heatmap',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)'
        });
    }

    createEmotionVisualization(data) {
        // Set up visualization area
        const visualizationArea = document.getElementById('visualization-area');
        visualizationArea.innerHTML = `
            <div id="emotion-timeline" style="height: 400px;"></div>
        `;

        // Create timeline trace
        const timelineTrace = {
            x: data.map(d => parseFloat(d.Time)),
            y: data.map(d => d['Emotion Predicted']),
            mode: 'lines+markers',
            type: 'scatter',
            name: 'Emotions',
            line: {
                shape: 'hv'
            },
            marker: {
                size: 8
            }
        };

        // Create plot
        Plotly.newPlot('emotion-timeline', [timelineTrace], {
            title: 'Emotion Timeline',
            xaxis: {
                title: 'Time (seconds)',
                tickformat: '.1f'
            },
            yaxis: {
                title: 'Emotion'
            },
            showlegend: false,
            margin: { l: 50, r: 50, t: 50, b: 50 }
        });
    }

    createAuraVisualization(data) {
        // Filter out invalid rows and parse data
        const validData = data
            .filter(d => d && d.timestamp)
            .map(d => {
                const parsed = { timestamp: parseFloat(d.timestamp) };
                Object.keys(d).forEach(key => {
                    if (key !== 'timestamp') {
                        parsed[key] = parseFloat(d[key]);
                    }
                });
                return parsed;
            })
            .filter(d => !isNaN(d.timestamp));

        if (validData.length === 0) {
            const visualizationArea = document.getElementById('visualization-area');
            visualizationArea.innerHTML = '<p class="error">No valid AURA data found</p>';
            return;
        }

        // Set up visualization area
        const visualizationArea = document.getElementById('visualization-area');
        visualizationArea.innerHTML = `
            <div id="aura-signals" style="height: 600px;"></div>
            <div id="aura-heatmap" style="height: 400px; margin-top: 20px;"></div>
        `;

        // Group signals by type
        const signalGroups = {
            Delta: Object.keys(validData[0]).filter(k => k.startsWith('Delta_')),
            Theta: Object.keys(validData[0]).filter(k => k.startsWith('Theta_')),
            Alpha: Object.keys(validData[0]).filter(k => k.startsWith('Alpha_')),
            Beta: Object.keys(validData[0]).filter(k => k.startsWith('Beta_')),
            Gamma: Object.keys(validData[0]).filter(k => k.startsWith('Gamma_'))
        };

        // Create traces for each signal
        const traces = [];
        Object.entries(signalGroups).forEach(([group, signals]) => {
            signals.forEach(signal => {
                traces.push({
                    x: validData.map(d => d.timestamp),
                    y: validData.map(d => d[signal]),
                    name: signal,
                    type: 'scatter',
                    mode: 'lines',
                    legendgroup: group,
                    line: { width: 1 }
                });
            });
        });

        // Create heatmap data
        const signalNames = Object.values(signalGroups).flat();
        const heatmapData = validData.map(d => 
            signalNames.map(signal => d[signal])
        );

        const heatmapTrace = {
            z: heatmapData,
            x: validData.map(d => d.timestamp),
            y: signalNames,
            type: 'heatmap',
            colorscale: 'Viridis'
        };

        // Create plots
        Plotly.newPlot('aura-signals', traces, {
            title: 'AURA Signals Over Time',
            xaxis: { 
                title: 'Time (seconds)',
                tickformat: '.1f'
            },
            yaxis: { 
                title: 'Signal Value'
            },
            showlegend: true,
            legend: {
                groupclick: 'toggleitem'
            },
            margin: { l: 50, r: 50, t: 50, b: 50 }
        });

        Plotly.newPlot('aura-heatmap', [heatmapTrace], {
            title: 'AURA Signal Heatmap',
            xaxis: { 
                title: 'Time (seconds)',
                tickformat: '.1f'
            },
            yaxis: { 
                title: 'Signal'
            },
            margin: { l: 100, r: 50, t: 50, b: 50 }
        });
    }

    createPointerVisualization(data) {
        const screenWidth = window.screen.width || 1920;
        const screenHeight = window.screen.height || 1080;

        // Parse the data
        const parsedData = data.map(d => ({
            timestamp: parseFloat(d.timestamp),
            x: Math.max(0, parseFloat(d.x)),
            y: Math.max(0, parseFloat(d.y)),
            clicked: parseInt(d.clicked)
        }));

        // Calculate display dimensions
        const maxX = Math.max(...parsedData.map(d => d.x));
        const maxY = Math.max(...parsedData.map(d => d.y));
        const displayWidth = Math.max(screenWidth, maxX);
        const displayHeight = Math.max(screenHeight, maxY);

        // Create movement trace
        const movementTrace = {
            x: parsedData.map(d => d.x),
            y: parsedData.map(d => d.y),
            mode: 'lines',
            type: 'scatter',
            line: {
                color: 'rgba(70, 130, 180, 0.6)',
                width: 2
            },
            name: 'Mouse Movement',
            hovertemplate: 'Time: %{text}<br>X: %{x}<br>Y: %{y}',
            text: parsedData.map(d => d.timestamp.toFixed(2))
        };

        // Create click trace
        const clickData = parsedData.filter(d => d.clicked === 1);
        const clickTrace = {
            x: clickData.map(d => d.x),
            y: clickData.map(d => d.y),
            mode: 'markers',
            type: 'scatter',
            marker: {
                symbol: 'circle',
                size: 10,
                color: 'red'
            },
            name: 'Clicks',
            hovertemplate: 'Click at:<br>Time: %{text}<br>X: %{x}<br>Y: %{y}',
            text: clickData.map(d => d.timestamp.toFixed(2))
        };

        // Create heatmap trace
        const heatmapTrace = {
            x: parsedData.map(d => d.x),
            y: parsedData.map(d => d.y),
            type: 'histogram2d',
            colorscale: [
                [0, 'rgba(0,0,0,0)'],
                [0.2, 'rgba(0,0,255,0.3)'],
                [0.4, 'rgba(0,255,255,0.5)'],
                [0.6, 'rgba(0,255,0,0.7)'],
                [0.8, 'rgba(255,255,0,0.8)'],
                [1.0, 'rgba(255,0,0,1)']
            ],
            nbinsx: 50,
            nbinsy: 50,
            name: 'Movement Density',
            showscale: true,
            zsmooth: 'best'
        };

        // Set up visualization area
        const visualizationArea = document.getElementById('visualization-area');
        visualizationArea.innerHTML = `
            <div id="pointer-combined" style="height: 400px; margin-bottom: 20px;"></div>
            <div id="pointer-heatmap" style="height: 400px;"></div>
        `;

        // Common layout settings
        const commonLayout = {
            xaxis: {
                title: 'X Position',
                range: [0, displayWidth],
                showgrid: true,
                gridcolor: 'rgba(128,128,128,0.2)'
            },
            yaxis: {
                title: 'Y Position',
                range: [displayHeight, 0],
                showgrid: true,
                gridcolor: 'rgba(128,128,128,0.2)',
                scaleanchor: 'x',
                scaleratio: 1
            },
            hovermode: 'closest',
            showlegend: true,
            margin: { l: 50, r: 50, t: 50, b: 50 }
        };

        // Create plots
        Plotly.newPlot('pointer-combined', [heatmapTrace, movementTrace, clickTrace], {
            ...commonLayout,
            title: 'Mouse Movement, Clicks, and Density'
        });

        Plotly.newPlot('pointer-heatmap', [heatmapTrace], {
            ...commonLayout,
            title: 'Mouse Movement Density Heatmap'
        });
    }
}

// Add error handling for script loading
window.addEventListener('error', (event) => {
    console.error('Script error:', event.error);
});

// Wrap the initialization in a try-catch
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('DOM Content Loaded - initializing DataViewer');
        new DataViewer();
    } catch (error) {
        console.error('Error initializing DataViewer:', error);
    }
}); 
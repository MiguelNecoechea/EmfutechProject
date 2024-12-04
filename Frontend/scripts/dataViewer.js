class DataViewer {
    constructor() {
        console.log('DataViewer constructor called');
        if (typeof Plotly === 'undefined') {
            console.error('Plotly is not loaded!');
            document.body.innerHTML = '<div class="error">Error: Plotly library not available</div>';
            return;
        }
        this.participantData = null;
        
        // Create initial structure
        const dataContainer = document.querySelector('.data-container');
        dataContainer.innerHTML = `
            <div class="video-section">
                <div class="video-container"></div>
            </div>
            <div class="visualization-section">
                <div class="visualization-controls">
                    <select id="data-type-selector"></select>
                    <button id="refresh-data">Refresh</button>
                </div>
                <div id="visualization-area"></div>
            </div>
        `;
        
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
        });
    }

    initializeUI() {
        console.log('Initializing UI');
    }

    async displayParticipantInfo() {
        if (!this.participantData) {
            console.error('No participant data available');
            return;
        }

        try {
            // Get available data files first
            const response = await window.electronAPI.getParticipantData({
                folderPath: this.participantData.folderPath,
                dataType: 'all'
            });

            if (response.status !== 'success') {
                throw new Error(response.message);
            }

            // Map file types to display names
            const fileTypeMap = {
                'gaze': 'Eye Tracking',
                'emotions': 'Emotion',
                'aura': 'AURA',
                'data': 'Mouse/Keyboard'
            };

            // Create options only for available data types
            const availableTypes = response.data.files
                .filter(file => file.type in fileTypeMap)
                .map(file => `<option value="${file.type === 'emotions' ? 'emotion' : 
                                   file.type === 'data' ? 'pointer' : 
                                   file.type}">${fileTypeMap[file.type]}</option>`)
                .join('');

            if (!availableTypes) {
                const visualizationArea = document.getElementById('visualization-area');
                visualizationArea.innerHTML = `<div class="no-data-message">No data files available</div>`;
                return;
            }

            // Update the selector with available options
            const selector = document.getElementById('data-type-selector');
            if (selector) {
                selector.innerHTML = availableTypes;
                this.setupEventListeners();
                await this.loadData();
            }

        } catch (error) {
            console.error('Error loading available data types:', error);
            const visualizationArea = document.getElementById('visualization-area');
            visualizationArea.innerHTML = `<div class="error-message">Error loading data: ${error.message}</div>`;
        }
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
        const selector = document.getElementById('data-type-selector');
        if (selector && selector.value) {
            await this.loadData();
        }
    }

    async loadData() {
        const selector = document.getElementById('data-type-selector');
        const dataType = selector.value;
        console.log('Loading data for type:', dataType);
        
        // Store the current options HTML before rebuilding
        const currentOptions = selector.innerHTML;
        
        // Update the data-container structure with top-bottom layout
        const dataContainer = document.querySelector('.data-container');
        dataContainer.innerHTML = `
            <div class="video-section">
                <div class="video-container"></div>
            </div>
            <div class="visualization-section">
                <div class="visualization-controls">
                    <select id="data-type-selector">${currentOptions}</select>
                    <button id="refresh-data">Refresh</button>
                </div>
                <div id="visualization-area"></div>
            </div>
        `;
        
        // Restore the selected value and event listeners
        const newSelector = document.getElementById('data-type-selector');
        newSelector.value = dataType;
        this.setupEventListeners();
        
        try {
            const response = await window.electronAPI.getParticipantData({
                folderPath: this.participantData.folderPath,
                dataType: dataType
            });

            if (response.status !== 'success') {
                throw new Error(response.message);
            }

            // Debug logs for video loading
            console.log('Response data files:', response.data.files);
            
            // Load video if available
            const videoContainer = document.querySelector('.video-container');
            const videoFiles = response.data.files.filter(f => 
                f.name.toLowerCase().includes('_heatmap.mp4') || 
                f.name.toLowerCase().includes('_screen.mp4')
            );
            console.log('Found video files:', videoFiles);
            
            if (videoFiles.length > 0) {
                console.log('Loading video...');
                
                // Prefer heatmap video if available
                const videoFile = videoFiles.find(f => f.name.toLowerCase().includes('_heatmap.mp4')) || videoFiles[0];
                const fileSizeMB = Math.round(videoFile.size / (1024 * 1024));
                
                videoContainer.innerHTML = `
                    <div class="loading-message">
                        Loading video (${fileSizeMB}MB)... This may take a moment for larger files.
                        <div class="loading-spinner"></div>
                        ${fileSizeMB > 100 ? '<div class="warning">Large file detected. If video fails to load, try converting it to a smaller file size.</div>' : ''}
                    </div>
                `;

                const videoHtml = `
                    <video controls width="100%" preload="metadata" id="data-video">
                        <source src="file:///${videoFile.path.replace(/\\/g, '/')}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                `;
                
                // Replace loading indicator with video element
                setTimeout(() => {
                    console.log('Setting video HTML:', videoHtml);
                    videoContainer.innerHTML = videoHtml;
                    
                    const videoElement = document.getElementById('data-video');
                    if (videoElement) {
                        // Add time update listener for emotion plots if they exist
                        if (this.emotionPlots) {
                            videoElement.addEventListener('timeupdate', () => {
                                const currentTime = videoElement.currentTime;
                                this.updateEmotionTimeLine(currentTime);
                            });

                            videoElement.addEventListener('seeking', () => {
                                const currentTime = videoElement.currentTime;
                                this.updateEmotionTimeLine(currentTime);
                            });
                        }

                        // Add error handler
                        videoElement.addEventListener('error', (e) => {
                            console.error('Video error:', e);
                            const error = videoElement.error;
                            if (error) {
                                console.error('Error code:', error.code);
                                console.error('Error message:', error.message);
                                videoContainer.innerHTML = `
                                    <div class="error-message">
                                        Error loading video (${fileSizeMB}MB file): ${error.message || 'Unknown error'}
                                        <br>
                                        <small>
                                            Suggestions:
                                            <ul>
                                                <li>Convert the video to a smaller file size (recommended: under 100MB)</li>
                                                <li>Try a different video format (e.g., WebM or compressed MP4)</li>
                                                <li>Reduce the video resolution</li>
                                            </ul>
                                        </small>
                                    </div>
                                `;
                            }
                        });
                    }
                }, 100); // Small delay to ensure loading indicator shows
            } else {
                console.log('No video files found');
                videoContainer.innerHTML = `<div class="no-video-message">No video recording available</div>`;
            }

            // Fix the file type mapping to match exactly what's in the file list
            const fileTypeMap = {
                gaze: 'gaze',
                emotion: 'emotions',
                aura: 'aura',
                pointer: 'data',
                face_landmarks: 'landmarks'
            };

            const fileType = fileTypeMap[dataType];
            console.log('Looking for file type:', fileType);
            
            const file = response.data.files.find(f => f.type === fileType);
            console.log('Found file:', file);
            
            if (!file) {
                throw new Error(`No ${dataType} data found`);
            }

            // Normalize file path for Windows
            const normalizedPath = file.path.replace(/\\/g, '/');
            console.log('Normalized file path:', normalizedPath);
            
            const csvData = await fetch(`file:///${normalizedPath}`);
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
            const visualizationArea = document.getElementById('visualization-area');
            visualizationArea.innerHTML = `
                <p class="error">Error loading data: ${error.message}</p>
                <p class="error-details">File path: ${file?.path}</p>
            `;
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
        // Get unique emotions and sort them
        const uniqueEmotions = [...new Set(data.map(d => d['Emotion Predicted']))].sort();
        
        // Set up visualization area with full width
        const visualizationArea = document.getElementById('visualization-area');
        visualizationArea.innerHTML = uniqueEmotions.map(emotion => 
            `<div id="emotion-${emotion.toLowerCase()}" style="width: 100%; height: 300px; margin-bottom: 20px;"></div>`
        ).join('');

        // Store plot references for updating
        this.emotionPlots = {};

        // Create individual plots for each emotion
        uniqueEmotions.forEach(emotion => {
            const trace = {
                x: data.map(d => parseFloat(d.Time)),
                y: data.map(d => d['Emotion Predicted'] === emotion ? 1 : 0),
                mode: 'lines',
                type: 'scatter',
                name: emotion,
                line: {
                    shape: 'hv',
                    width: 2
                },
                fill: 'tozeroy'
            };

            // Add vertical line trace
            const timeLine = {
                x: [0, 0],
                y: [-0.1, 1.1],
                mode: 'lines',
                name: 'Current Time',
                line: {
                    color: 'red',
                    width: 2,
                    dash: 'dot'
                },
                hoverinfo: 'none'
            };

            const layout = {
                title: `${emotion} Timeline`,
                xaxis: {
                    title: 'Time (seconds)',
                    tickformat: '.1f'
                },
                yaxis: {
                    title: 'Present',
                    range: [-0.1, 1.1],
                    tickvals: [0, 1],
                    ticktext: ['No', 'Yes']
                },
                margin: { l: 50, r: 30, t: 50, b: 50 },
                autosize: true,
                showlegend: false
            };

            const config = {
                responsive: true,
                displayModeBar: false
            };

            Plotly.newPlot(`emotion-${emotion.toLowerCase()}`, [trace, timeLine], layout, config);
            this.emotionPlots[emotion] = document.getElementById(`emotion-${emotion.toLowerCase()}`);
        });

        // Add video time update listener
        const video = document.querySelector('video');
        if (video) {
            video.addEventListener('timeupdate', () => {
                const currentTime = video.currentTime;
                this.updateEmotionTimeLine(currentTime);
            });

            // Add seeking listener for smooth updates while dragging
            video.addEventListener('seeking', () => {
                const currentTime = video.currentTime;
                this.updateEmotionTimeLine(currentTime);
            });
        }
    }

    updateEmotionTimeLine(currentTime) {
        // Update the vertical line position in all emotion plots
        Object.values(this.emotionPlots).forEach(plot => {
            const update = {
                'x': [[currentTime, currentTime]]  // Update x coordinates of the line
            };
            Plotly.update(plot, update, {}, [1]);  // Update only the second trace (the time line)
        });
    }

    createAuraVisualization(data) {
        // Filter out invalid rows and parse data
        const validData = data
            .filter(d => d && d.timestamp)
            .map(d => {
                const parsed = { 
                    timestamp: parseFloat(d.timestamp),
                    ...Object.keys(d)
                        .filter(key => key.startsWith('ConcentrationIndex_'))
                        .reduce((obj, key) => {
                            obj[key] = parseFloat(d[key]);
                            return obj;
                        }, {})
                };
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
            <div id="concentration-timeline" style="height: 600px;"></div>
        `;

        // Create traces for each concentration index with distinct colors
        const colors = [
            '#1f77b4', // blue
            '#ff7f0e', // orange
            '#2ca02c', // green
            '#d62728', // red
            '#9467bd', // purple
            '#8c564b', // brown
            '#e377c2', // pink
            '#7f7f7f'  // gray
        ];

        const concentrationChannels = Object.keys(validData[0])
            .filter(key => key.startsWith('ConcentrationIndex_'));
        
        const traces = concentrationChannels.map((channel, index) => ({
            x: validData.map(d => d.timestamp),
            y: validData.map(d => d[channel]),
            name: channel.replace('ConcentrationIndex_', ''),
            type: 'scatter',
            mode: 'lines',
            line: { 
                width: 2.5,
                color: colors[index % colors.length],
                shape: 'spline' // Makes the lines smoother
            }
        }));

        // Add reference line at y=1
        const referenceLine = {
            x: [Math.min(...validData.map(d => d.timestamp)), 
                Math.max(...validData.map(d => d.timestamp))],
            y: [1, 1],
            mode: 'lines',
            name: 'Reference Level',
            line: {
                color: 'rgba(128, 128, 128, 0.5)',
                width: 2,
                dash: 'dash'
            },
            hoverinfo: 'none'
        };

        // Create plot with improved styling
        Plotly.newPlot('concentration-timeline', [...traces, referenceLine], {
            title: {
                text: 'Concentration Indices Over Time',
                font: { size: 24 }
            },
            xaxis: { 
                title: 'Time (seconds)',
                tickformat: '.1f',
                gridcolor: 'rgba(128, 128, 128, 0.2)'
            },
            yaxis: { 
                title: 'Concentration Index',
                range: [0, Math.max(2, ...traces.flatMap(t => t.y))] // Set range from 0 to max value or 2
            },
            showlegend: true,
            legend: {
                title: { text: 'Channels' }
            },
            margin: { l: 50, r: 50, t: 50, b: 50 }
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
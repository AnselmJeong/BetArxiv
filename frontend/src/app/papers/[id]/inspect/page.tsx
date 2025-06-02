import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import PDFViewer from '@/components/PDFViewer';

export default function PaperInspectPage() {
  return (
    <div className="h-full bg-muted/50 flex flex-col">
      <div className="max-w-7xl mx-auto py-6 px-4 flex-1 flex flex-col min-h-0">
        <div className="text-sm text-muted-foreground mb-4">
          <span className="mr-2">Papers</span>/ <span className="ml-2">Paper Title</span>
        </div>
        <div className="flex gap-6 flex-1 min-h-0">
          {/* PDF Viewer - 60% width */}
          <Card className="w-3/5 overflow-hidden">
            <PDFViewer pdfUrl="/sample.pdf" className="h-full" />
          </Card>
          {/* Metadata and Summary - 40% width */}
          <div className="w-2/5 flex flex-col min-h-0">
            <Card className="flex-1 p-6 flex flex-col min-h-[600px]">
              <h1 className="text-3xl font-bold mb-4">Paper Title</h1>
              <div className="text-muted-foreground mb-6">Authors: Author 1, Author 2, Author 3</div>
              <div className="mb-6">
                <h2 className="font-semibold text-lg mb-2">Abstract</h2>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  This paper explores the application of machine learning techniques in the field of environmental science. 
                  It focuses on predicting air quality using various meteorological parameters and pollutant concentrations. 
                  Results demonstrate significant improvements over traditional methods with potential implications for urban planning. 
                  The research contributes to the growing body of knowledge in environmental monitoring and provides practical 
                  solutions for real-world air quality prediction challenges.
                </p>
              </div>
              <Tabs defaultValue="distinction" className="w-full flex-1 flex flex-col">
                <TabsList className="grid grid-cols-3 mb-4">
                  <TabsTrigger value="distinction">Distinction</TabsTrigger>
                  <TabsTrigger value="methodology">Methodology</TabsTrigger>
                  <TabsTrigger value="results">Results</TabsTrigger>
                </TabsList>
                <TabsContent value="distinction" className="flex-1">
                  <h3 className="font-semibold mb-2">Distinction</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    This study stands out by integrating advanced machine learning techniques with traditional time series analysis, 
                    offering a more nuanced approach to air quality prediction. Unlike previous studies that relied solely on 
                    historical data patterns, this research incorporates real-time meteorological variables and advanced ensemble 
                    methods to improve prediction accuracy. The novel integration of deep learning architectures with traditional 
                    statistical models provides a comprehensive framework that addresses the limitations of existing approaches.
                  </p>
                </TabsContent>
                <TabsContent value="methodology" className="flex-1">
                  <h3 className="font-semibold mb-2">Methodology</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    The methodology employs a hybrid approach combining LSTM neural networks with ARIMA models to capture both 
                    temporal dependencies and seasonal patterns in air quality data. Data preprocessing includes feature engineering 
                    of meteorological variables, outlier detection, and normalization techniques. The model training process 
                    utilizes cross-validation with temporal splits to ensure robust performance evaluation. Hyperparameter 
                    optimization is conducted using Bayesian optimization techniques to achieve optimal model configuration.
                  </p>
                </TabsContent>
                <TabsContent value="results" className="flex-1">
                  <h3 className="font-semibold mb-2">Results</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    The proposed model achieved a 23% improvement in RMSE compared to baseline methods, with particularly 
                    strong performance during high pollution episodes. Accuracy metrics show consistent performance across 
                    different seasons and weather conditions. Feature importance analysis reveals that wind direction and 
                    atmospheric pressure are the most significant predictors. The model demonstrates robust generalization 
                    capabilities when tested on data from different geographic locations within the same urban area.
                  </p>
                </TabsContent>
              </Tabs>
            </Card>
            <div className="flex justify-center gap-4 mt-6">
              <Button variant="secondary" className="px-6">Update Metadata</Button>
              <Button className="px-6">Update Summary</Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 
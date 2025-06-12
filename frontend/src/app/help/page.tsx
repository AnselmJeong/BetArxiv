import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { API_CONFIG } from "@/config/api";

export default function HelpPage() {
  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">도움말</h1>
        <p className="text-xl text-muted-foreground">
          BetArxiv 연구 논문 지식 추출 플랫폼 사용 가이드
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📚 논문 검색
              <Badge variant="secondary">핵심 기능</Badge>
            </CardTitle>
            <CardDescription>
              AI 기반 의미론적 검색과 키워드 검색
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <h4 className="font-medium">의미론적 검색</h4>
              <p className="text-sm text-muted-foreground">
                자연어로 질문하면 관련 논문을 찾아줍니다
              </p>
            </div>
            <div>
              <h4 className="font-medium">키워드 검색</h4>
              <p className="text-sm text-muted-foreground">
                특정 키워드로 정확한 검색이 가능합니다
              </p>
            </div>
            <Button asChild variant="outline" size="sm">
              <Link href="/search">검색 시작하기</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              💬 AI 채팅
              <Badge variant="secondary">AI 기능</Badge>
            </CardTitle>
            <CardDescription>
              논문 내용에 대해 AI와 대화하기
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <h4 className="font-medium">논문 분석</h4>
              <p className="text-sm text-muted-foreground">
                논문의 주요 내용을 요약하고 설명합니다
              </p>
            </div>
            <div>
              <h4 className="font-medium">질의응답</h4>
              <p className="text-sm text-muted-foreground">
                논문에 대한 궁금한 점을 물어보세요
              </p>
            </div>
            <Button asChild variant="outline" size="sm">
              <Link href="/papers">논문 보기</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📊 논문 관리
              <Badge variant="secondary">관리 기능</Badge>
            </CardTitle>
            <CardDescription>
              논문 정리 및 평가 시스템
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <h4 className="font-medium">폴더 관리</h4>
              <p className="text-sm text-muted-foreground">
                주제별로 논문을 분류하고 정리합니다
              </p>
            </div>
            <div>
              <h4 className="font-medium">평점 시스템</h4>
              <p className="text-sm text-muted-foreground">
                논문의 중요도와 품질을 평가할 수 있습니다
              </p>
            </div>
            <Button asChild variant="outline" size="sm">
              <Link href="/archive">아카이브 보기</Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>🔧 API 정보</CardTitle>
          <CardDescription>
            개발자를 위한 API 엔드포인트 정보
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="font-medium mb-2">주요 엔드포인트</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• <code>/api/documents</code> - 논문 목록</li>
                <li>• <code>/api/documents/search</code> - 논문 검색</li>
                <li>• <code>/api/documents/folders</code> - 폴더 목록</li>
                <li>• <code>/api/documents/[id]/chat</code> - AI 채팅</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">API 문서</h4>
              <div className="space-y-2">
                <Button asChild variant="outline" size="sm" className="w-full">
                  <Link href={`${API_CONFIG.baseUrl}/docs`} target="_blank">
                    Swagger UI 문서
                  </Link>
                </Button>
                <Button asChild variant="outline" size="sm" className="w-full">
                  <Link href={`${API_CONFIG.baseUrl}/help`} target="_blank">
                    API 도움말
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>❓ 자주 묻는 질문</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium">Q: 논문을 어떻게 추가하나요?</h4>
            <p className="text-sm text-muted-foreground mt-1">
              A: 현재 버전에서는 관리자가 서버에 직접 PDF를 업로드하는 방식입니다. 향후 웹 업로드 기능이 추가될 예정입니다.
            </p>
          </div>
          <div>
            <h4 className="font-medium">Q: 검색이 제대로 되지 않아요</h4>
            <p className="text-sm text-muted-foreground mt-1">
              A: 의미론적 검색은 자연어로, 키워드 검색은 정확한 단어로 시도해보세요. 영어와 한국어 모두 지원됩니다.
            </p>
          </div>
          <div>
            <h4 className="font-medium">Q: AI 채팅이 느려요</h4>
            <p className="text-sm text-muted-foreground mt-1">
              A: AI 모델 처리 시간에 따라 응답이 지연될 수 있습니다. 네트워크 상태도 확인해주세요.
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="text-center">
        <p className="text-sm text-muted-foreground">
          더 자세한 정보가 필요하시면{" "}
          <Link href="/" className="text-primary hover:underline">
            메인 페이지
          </Link>
          로 돌아가서 각 기능을 직접 사용해보세요.
        </p>
      </div>
    </div>
  );
} 
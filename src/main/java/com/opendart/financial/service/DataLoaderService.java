package com.opendart.financial.service;

import com.opendart.financial.entity.Corporation;
import com.opendart.financial.repository.CorporationRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Service;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.File;

/**
 * corp.xml 파일을 읽어서 데이터베이스에 로드하는 서비스
 */
@Service
public class DataLoaderService implements CommandLineRunner {
    
    @Autowired
    private CorporationRepository corporationRepository;
    
    @Override
    public void run(String... args) throws Exception {
        // 데이터베이스에 데이터가 이미 있는지 확인
        if (corporationRepository.count() > 0) {
            System.out.println("데이터가 이미 로드되어 있습니다. 총 " + corporationRepository.count() + "개 기업");
            return;
        }
        
        System.out.println("corp.xml 파일을 읽어서 데이터베이스에 로드 중...");
        loadCorporationData();
        System.out.println("데이터 로드 완료! 총 " + corporationRepository.count() + "개 기업");
    }
    
    /**
     * corp.xml 파일을 파싱하여 데이터베이스에 저장
     */
    private void loadCorporationData() {
        try {
            File xmlFile = new File("corp.xml");
            if (!xmlFile.exists()) {
                System.err.println("corp.xml 파일을 찾을 수 없습니다.");
                return;
            }
            
            DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
            DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();
            Document doc = dBuilder.parse(xmlFile);
            doc.getDocumentElement().normalize();
            
            NodeList listNodes = doc.getElementsByTagName("list");
            
            for (int i = 0; i < listNodes.getLength(); i++) {
                Element listElement = (Element) listNodes.item(i);
                
                String corpCode = getElementValue(listElement, "corp_code");
                String corpName = getElementValue(listElement, "corp_name");
                String corpEngName = getElementValue(listElement, "corp_eng_name");
                String stockCode = getElementValue(listElement, "stock_code");
                String modifyDate = getElementValue(listElement, "modify_date");
                
                // 빈 값들을 null로 처리
                if (corpEngName != null && corpEngName.trim().isEmpty()) {
                    corpEngName = null;
                }
                if (stockCode != null && stockCode.trim().isEmpty()) {
                    stockCode = null;
                }
                
                Corporation corporation = new Corporation(corpCode, corpName, corpEngName, stockCode, modifyDate);
                corporationRepository.save(corporation);
                
                // 진행 상황 출력 (1000개마다)
                if ((i + 1) % 1000 == 0) {
                    System.out.println("처리된 기업 수: " + (i + 1));
                }
            }
            
        } catch (Exception e) {
            System.err.println("XML 파일 처리 중 오류 발생: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * XML 엘리먼트에서 값을 추출하는 헬퍼 메소드
     */
    private String getElementValue(Element parent, String tagName) {
        NodeList nodeList = parent.getElementsByTagName(tagName);
        if (nodeList.getLength() > 0) {
            return nodeList.item(0).getTextContent();
        }
        return null;
    }
}

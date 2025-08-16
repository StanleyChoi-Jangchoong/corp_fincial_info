package com.opendart.financial.entity;

import jakarta.persistence.*;

/**
 * 기업 정보 엔티티
 */
@Entity
@Table(name = "corporations")
public class Corporation {
    
    @Id
    @Column(name = "corp_code", length = 8)
    private String corpCode;
    
    @Column(name = "corp_name", nullable = false)
    private String corpName;
    
    @Column(name = "corp_eng_name")
    private String corpEngName;
    
    @Column(name = "stock_code", length = 6)
    private String stockCode;
    
    @Column(name = "modify_date", length = 8)
    private String modifyDate;
    
    // 기본 생성자
    public Corporation() {}
    
    // 생성자
    public Corporation(String corpCode, String corpName, String corpEngName, 
                      String stockCode, String modifyDate) {
        this.corpCode = corpCode;
        this.corpName = corpName;
        this.corpEngName = corpEngName;
        this.stockCode = stockCode;
        this.modifyDate = modifyDate;
    }
    
    // Getters and Setters
    public String getCorpCode() {
        return corpCode;
    }
    
    public void setCorpCode(String corpCode) {
        this.corpCode = corpCode;
    }
    
    public String getCorpName() {
        return corpName;
    }
    
    public void setCorpName(String corpName) {
        this.corpName = corpName;
    }
    
    public String getCorpEngName() {
        return corpEngName;
    }
    
    public void setCorpEngName(String corpEngName) {
        this.corpEngName = corpEngName;
    }
    
    public String getStockCode() {
        return stockCode;
    }
    
    public void setStockCode(String stockCode) {
        this.stockCode = stockCode;
    }
    
    public String getModifyDate() {
        return modifyDate;
    }
    
    public void setModifyDate(String modifyDate) {
        this.modifyDate = modifyDate;
    }
    
    @Override
    public String toString() {
        return "Corporation{" +
                "corpCode='" + corpCode + '\'' +
                ", corpName='" + corpName + '\'' +
                ", corpEngName='" + corpEngName + '\'' +
                ", stockCode='" + stockCode + '\'' +
                ", modifyDate='" + modifyDate + '\'' +
                '}';
    }
}

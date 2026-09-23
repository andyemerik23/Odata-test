from fastapi.responses import Response


METADATA_XML = """<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="4.0"
    xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">

    <edmx:DataServices>
        <Schema Namespace="ODataDemo"
            xmlns="http://docs.oasis-open.org/odata/ns/edm">

            <EntityType Name="Order">
                <Key>
                    <PropertyRef Name="Order_ID"/>
                </Key>

                <Property Name="Order_ID"
                    Type="Edm.String"
                    Nullable="false"/>

                <Property Name="Order_Date"
                    Type="Edm.DateTimeOffset"/>

                <Property Name="Customer_ID"
                    Type="Edm.String"/>

                <Property Name="City"
                    Type="Edm.String"/>

                <Property Name="Category"
                    Type="Edm.String"/>

                <Property Name="Channel"
                    Type="Edm.String"/>

                <Property Name="Quantity"
                    Type="Edm.Int32"/>

                <Property Name="Unit_Price"
                    Type="Edm.Double"/>

                <Property Name="Sales"
                    Type="Edm.Double"/>

                <Property Name="Status"
                    Type="Edm.String"/>
            </EntityType>

            <EntityContainer Name="Container">
                <EntitySet Name="Orders"
                    EntityType="ODataDemo.Order"/>
            </EntityContainer>

        </Schema>
    </edmx:DataServices>

</edmx:Edmx>
"""


def metadata_response():
    return Response(
        content=METADATA_XML,
        media_type="application/xml"
    )